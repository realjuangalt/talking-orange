/**
 * MindAR Target Image Compiler Script
 * Compiles a single image to .mind file using Puppeteer to automate the web compiler
 * 
 * The MindAR compiler uses custom TensorFlow.js kernels that are only available
 * in the browser WebGL backend, not in Node.js. So we use Puppeteer to run it
 * in a real browser environment.
 * 
 * Usage: node compile_target.js <input_image> <output.mind>
 */

import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';

async function compileImage(inputPath, outputPath) {
    let browser;
    try {
        console.error(`🔄 Compiling ${path.basename(inputPath)} to ${path.basename(outputPath)}...`);
        
        // Launch browser
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        });
        
        const page = await browser.newPage();
        
        // Set up download interception using CDP (Chrome DevTools Protocol)
        const downloadPath = path.dirname(outputPath);
        const client = await page.target().createCDPSession();
        await client.send('Page.setDownloadBehavior', {
            behavior: 'allow',
            downloadPath: downloadPath
        });
        
        // Monitor network requests to catch blob URL creation
        const blobUrls = [];
        page.on('response', async (response) => {
            const url = response.url();
            if (url.startsWith('blob:')) {
                blobUrls.push(url);
                console.error(`📦 Detected blob URL: ${url.substring(0, 50)}...`);
            }
        });
        
        // Navigate to the MindAR compiler page
        const compilerUrl = 'https://hiukim.github.io/mind-ar-js-doc/tools/compile';
        console.error(`📡 Loading compiler page: ${compilerUrl}`);
        await page.goto(compilerUrl, { 
            waitUntil: 'networkidle2', 
            timeout: 30000 
        });
        
        // Wait for the file input to be available
        console.error('⏳ Waiting for compiler to load...');
        await page.waitForSelector('input[type="file"]', { timeout: 30000 });
        
        // Give the compiler a moment to fully initialize
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Upload the image file
        const fileInput = await page.$('input[type="file"]');
        if (!fileInput) {
            throw new Error('File input not found on compiler page');
        }
        
        console.error(`📤 Uploading image: ${path.basename(inputPath)}`);
        await fileInput.uploadFile(inputPath);
        
        // Wait a moment for the file to be processed
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Set up console message listener to catch compilation completion
        const consoleMessages = [];
        page.on('console', msg => {
            const text = msg.text();
            consoleMessages.push(text);
            if (text.includes('complete') || text.includes('done') || text.includes('ready') || text.includes('download')) {
                console.error(`📢 Console message: ${text}`);
            }
        });
        
        // Wait for compilation to complete
        // The compiler typically completes in 5-30 seconds for most images
        console.error('⏳ Waiting for compilation to complete (checking every 0.5s)...');
        
        // Monitor page for completion - check multiple indicators
        let downloadInfo = null;
        let attempts = 0;
        const maxAttempts = 60; // 60 seconds max (compilation is usually fast, but allow buffer)
        
        while (attempts < maxAttempts && !downloadInfo) {
            await new Promise(resolve => setTimeout(resolve, 500)); // Check every 0.5 seconds for faster detection
            
            downloadInfo = await page.evaluate(() => {
                // Method 1: Look for ANY blob URL anywhere (most reliable)
                // The compiler creates a blob URL when compilation is done
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const href = el.getAttribute('href');
                    if (href && href.startsWith('blob:')) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            return {
                                href: href,
                                download: el.getAttribute('download') || 'target.mind',
                                selector: 'any-blob-element',
                                text: el.textContent || el.tagName
                            };
                        }
                    }
                }
                
                // Method 2: Look for download links/buttons with specific selectors
                const downloadSelectors = [
                    'a[download]',
                    'a[href*=".mind"]',
                    'a[href^="blob:"]',
                    'button[download]',
                    'a[href*="download"]',
                    '[data-download]',
                    'a',  // Check all links
                    'button'  // Check all buttons
                ];
                
                for (const selector of downloadSelectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {
                        const href = element.getAttribute('href');
                        const disabled = element.hasAttribute('disabled') || element.classList.contains('disabled');
                        const text = (element.textContent || '').toLowerCase();
                        const style = window.getComputedStyle(element);
                        
                        // Check if element is visible and enabled
                        if (style.display !== 'none' && style.visibility !== 'hidden' && !disabled) {
                            // Check for blob URL
                            if (href && href.startsWith('blob:')) {
                                return {
                                    href: href,
                                    download: element.getAttribute('download') || 'target.mind',
                                    selector: selector,
                                    text: element.textContent
                                };
                            }
                            // Check for .mind in href or download text
                            if (href && (href.includes('.mind') || text.includes('download') || text.includes('mind'))) {
                                return {
                                    href: href,
                                    download: element.getAttribute('download') || 'target.mind',
                                    selector: selector,
                                    text: element.textContent
                                };
                            }
                        }
                    }
                }
                
                // Method 3: Check window object for compiled data (some compilers store it globally)
                if (window.compiledData || window.targetData || window.downloadUrl) {
                    const data = window.compiledData || window.targetData || window.downloadUrl;
                    if (typeof data === 'string' && data.startsWith('blob:')) {
                        return {
                            href: data,
                            download: 'target.mind',
                            selector: 'window-object',
                            text: 'window.compiledData'
                        };
                    }
                }
                
                return null;
            });
            
            // Also check if we detected any blob URLs from network monitoring
            if (!downloadInfo && blobUrls.length > 0) {
                console.error(`📦 Using blob URL from network monitoring: ${blobUrls[blobUrls.length - 1].substring(0, 50)}...`);
                downloadInfo = {
                    href: blobUrls[blobUrls.length - 1],
                    download: 'target.mind',
                    selector: 'network-monitor',
                    text: 'Detected from network'
                };
            }
            
            if (downloadInfo) {
                console.error(`✅ Found download link! (after ${(attempts * 0.5).toFixed(1)}s)`);
                break;
            }
            
            attempts++;
            if (attempts % 4 === 0) {
                process.stderr.write(`\r⏳ Checking for completion... (${(attempts * 0.5).toFixed(1)}s)`);
            }
        }
        
        if (!downloadInfo) {
            // Get detailed debug info
            const debugInfo = await page.evaluate(() => {
                return {
                    allLinks: Array.from(document.querySelectorAll('a')).map(a => ({
                        href: a.getAttribute('href'),
                        text: a.textContent,
                        download: a.getAttribute('download'),
                        visible: window.getComputedStyle(a).display !== 'none'
                    })),
                    allButtons: Array.from(document.querySelectorAll('button')).map(b => ({
                        text: b.textContent,
                        disabled: b.disabled,
                        visible: window.getComputedStyle(b).display !== 'none'
                    })),
                    pageText: document.body.innerText.substring(0, 1000),
                    blobUrls: Array.from(document.querySelectorAll('*')).map(el => {
                        const href = el.getAttribute('href');
                        return href && href.startsWith('blob:') ? href : null;
                    }).filter(Boolean)
                };
            });
            
            console.error('\n⚠️  Download link not found after 60 seconds. Debug info:');
            console.error(`Found ${debugInfo.allLinks.length} links, ${debugInfo.allButtons.length} buttons`);
            console.error(`Blob URLs found: ${debugInfo.blobUrls.length}`);
            if (debugInfo.blobUrls.length > 0) {
                console.error('Blob URLs:', debugInfo.blobUrls);
            }
            console.error('Page text preview:', debugInfo.pageText.substring(0, 300));
            
            // Try to take a screenshot for debugging (save to temp location)
            try {
                const screenshotPath = outputPath.replace('.mind', '_debug_screenshot.png');
                await page.screenshot({ path: screenshotPath, fullPage: true });
                console.error(`📸 Debug screenshot saved to: ${screenshotPath}`);
            } catch (screenshotError) {
                // Ignore screenshot errors
            }
            
            throw new Error('Compilation may have completed but download link not found. Check debug screenshot for details.');
        }
        
        console.error('✅ Compilation complete! Downloading .mind file...');
        
        if (downloadInfo && downloadInfo.href) {
            console.error(`📥 Download link found: ${downloadInfo.href.substring(0, 50)}...`);
            
            if (downloadInfo.href.startsWith('blob:')) {
                // Handle blob URL - get the data via page evaluation
                console.error('📦 Extracting data from blob URL...');
                const buffer = await page.evaluate(async (blobUrl) => {
                    try {
                        const response = await fetch(blobUrl);
                        const blob = await response.blob();
                        const arrayBuffer = await blob.arrayBuffer();
                        return Array.from(new Uint8Array(arrayBuffer));
                    } catch (error) {
                        console.error('Error fetching blob:', error);
                        return null;
                    }
                }, downloadInfo.href);
                
                if (buffer && buffer.length > 0) {
                    fs.writeFileSync(outputPath, Buffer.from(buffer));
                    const fileSize = fs.statSync(outputPath).size;
                    console.error(`✅ Compilation successful! Output: ${path.basename(outputPath)} (${(fileSize / 1024).toFixed(2)} KB)`);
                    console.log('SUCCESS');
                    process.exit(0);
                } else {
                    throw new Error('Failed to extract data from blob URL');
                }
            } else {
                // Try clicking the download link
                console.error('🖱️  Clicking download link...');
                try {
                    await page.click(downloadInfo.selector || 'a[download], a[href*=".mind"]');
                } catch (clickError) {
                    // If click fails, try to trigger download programmatically
                    console.error('⚠️  Click failed, trying programmatic download...');
                    await page.evaluate((href) => {
                        const link = document.createElement('a');
                        link.href = href;
                        link.download = 'target.mind';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    }, downloadInfo.href);
                }
                
                // Wait for download to complete
                console.error('⏳ Waiting for download to complete...');
                for (let i = 0; i < 10; i++) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Check if file was downloaded
                    const files = fs.readdirSync(downloadPath)
                        .filter(f => f.endsWith('.mind'))
                        .map(f => ({
                            name: f,
                            path: path.join(downloadPath, f),
                            mtime: fs.statSync(path.join(downloadPath, f)).mtimeMs
                        }))
                        .sort((a, b) => b.mtime - a.mtime);
                    
                    if (files.length > 0) {
                        const downloadedFile = files[0].path;
                        console.error(`📥 Found downloaded file: ${files[0].name}`);
                        if (downloadedFile !== outputPath) {
                            fs.renameSync(downloadedFile, outputPath);
                        }
                        const stats = fs.statSync(outputPath);
                        console.error(`✅ Compilation successful! Output: ${path.basename(outputPath)} (${(stats.size / 1024).toFixed(2)} KB)`);
                        console.log('SUCCESS');
                        process.exit(0);
                    }
                }
                
                throw new Error('Download started but file not found in expected location');
            }
        }
        
        // If we get here, try alternative methods to get the compiled data
        console.error('⚠️  Standard download method failed, trying alternative approaches...');
        
        // Method 1: Check if there's a data URL or base64 data in the page
        const alternativeData = await page.evaluate(() => {
            // Look for any data URLs or base64 encoded data
            const scripts = Array.from(document.querySelectorAll('script'));
            for (const script of scripts) {
                const content = script.textContent || '';
                if (content.includes('blob:') || content.includes('data:')) {
                    // Try to extract blob URL
                    const blobMatch = content.match(/blob:[^\s"']+/);
                    if (blobMatch) {
                        return { type: 'blob', url: blobMatch[0] };
                    }
                }
            }
            
            // Check for any global variables that might contain the compiled data
            if (window.compiledData || window.targetData) {
                return { type: 'global', data: window.compiledData || window.targetData };
            }
            
            return null;
        });
        
        if (alternativeData) {
            console.error('📦 Found alternative data source');
            if (alternativeData.type === 'blob' && alternativeData.url) {
                const buffer = await page.evaluate(async (blobUrl) => {
                    const response = await fetch(blobUrl);
                    const blob = await response.blob();
                    const arrayBuffer = await blob.arrayBuffer();
                    return Array.from(new Uint8Array(arrayBuffer));
                }, alternativeData.url);
                
                if (buffer && buffer.length > 0) {
                    fs.writeFileSync(outputPath, Buffer.from(buffer));
                    console.error(`✅ Compilation successful! Output: ${path.basename(outputPath)} (${(buffer.length / 1024).toFixed(2)} KB)`);
                    console.log('SUCCESS');
                    process.exit(0);
                }
            }
        }
        
        // Get debug info
        const pageText = await page.evaluate(() => document.body.innerText).catch(() => 'Could not get page text');
        const allLinks = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.getAttribute('href'),
                text: a.textContent,
                download: a.getAttribute('download')
            }));
        }).catch(() => []);
        
        console.error('⚠️  Download link not found. Debug info:');
        console.error(`Page text preview: ${pageText.substring(0, 500)}`);
        console.error(`Found ${allLinks.length} links on page`);
        if (allLinks.length > 0) {
            console.error('Links found:', allLinks.slice(0, 5));
        }
        
        throw new Error('Could not download compiled file from compiler page. Compilation may have completed but download link is not accessible.');
    } catch (error) {
        console.error('ERROR:', error.message);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
    console.error('Usage: node compile_target.js <input_image> <output.mind>');
    console.error('');
    console.error('This script uses Puppeteer to automate the MindAR web compiler.');
    console.error('Compiler: https://hiukim.github.io/mind-ar-js-doc/tools/compile');
    process.exit(1);
}

if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found: ${inputPath}`);
    process.exit(1);
}

compileImage(inputPath, outputPath);
