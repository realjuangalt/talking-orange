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
        
        // Navigate to the MindAR compiler page
        const compilerUrl = 'https://hiukim.github.io/mind-ar-js-doc/tools/compile';
        console.error(`📡 Loading compiler page: ${compilerUrl}`);
        await page.goto(compilerUrl, { 
            waitUntil: 'networkidle2', 
            timeout: 60000 
        });
        
        // Wait a bit for the page to fully load JavaScript and initialize
        console.error('⏳ Waiting for compiler page to initialize...');
        await new Promise(resolve => setTimeout(resolve, 3000));
        
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
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Set up console message listener to catch compilation completion
        const consoleMessages = [];
        page.on('console', msg => {
            const text = msg.text();
            consoleMessages.push(text);
            if (text.includes('complete') || text.includes('done') || text.includes('ready') || text.includes('download') || text.includes('success')) {
                console.error(`📢 Console message: ${text}`);
            }
        });
        
        // Also monitor network responses for blob URLs
        page.on('response', async (response) => {
            const url = response.url();
            if (url.startsWith('blob:')) {
                blobUrls.push(url);
                console.error(`📦 Detected blob URL in response: ${url.substring(0, 50)}...`);
            }
        });
        
        // Wait for compilation to complete
        // The compiler typically completes in 5-30 seconds for most images
        console.error('⏳ Waiting for compilation to complete (checking every 0.5s)...');
        console.error('   The compiler will analyze your image and generate a .mind file.');
        console.error('   This usually takes 10-30 seconds depending on image complexity.');
        
        // Monitor page for completion - check multiple indicators
        let downloadInfo = null;
        let attempts = 0;
        const maxAttempts = 60; // 60 seconds max (compilation is usually fast, but allow buffer)
        
        while (attempts < maxAttempts && !downloadInfo) {
            await new Promise(resolve => setTimeout(resolve, 500)); // Check every 0.5 seconds for faster detection
            
            downloadInfo = await page.evaluate(() => {
                // PRIORITY 1: Look for blob URLs first (most reliable - these are the actual compiled files)
                // The compiler creates a blob URL when compilation is done
                const allElements = document.querySelectorAll('*');
                const blobUrls = [];
                for (const el of allElements) {
                    const href = el.getAttribute('href');
                    if (href && href.startsWith('blob:')) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            blobUrls.push({
                                href: href,
                                download: el.getAttribute('download') || 'target.mind',
                                selector: 'blob-element',
                                text: el.textContent || el.tagName,
                                element: el
                            });
                        }
                    }
                }
                
                // If we found blob URLs, use the one with download attribute or most recent
                if (blobUrls.length > 0) {
                    // Prefer blob URLs with download attribute
                    const withDownload = blobUrls.find(b => b.download && b.download.includes('.mind'));
                    if (withDownload) {
                        return withDownload;
                    }
                    // Otherwise use the last one (most recent)
                    return blobUrls[blobUrls.length - 1];
                }
                
                // PRIORITY 2: Look for download button/link (but exclude navigation links)
                const downloadButtons = Array.from(document.querySelectorAll('a, button')).filter(el => {
                    const text = (el.textContent || '').toLowerCase();
                    const href = el.getAttribute('href') || '';
                    const style = window.getComputedStyle(el);
                    const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                    const isEnabled = !el.disabled && !el.classList.contains('disabled');
                    
                    // CRITICAL: Exclude navigation links (they start with /mind-ar-js-doc or are relative paths)
                    const isNavigationLink = (href.startsWith('/') || href.startsWith('./') || href.startsWith('../')) && 
                                           !href.startsWith('blob:') && 
                                           !href.includes('.mind');
                    
                    return isVisible && isEnabled && !isNavigationLink && (
                        text.includes('download') || 
                        (text.includes('mind') && !text.includes('mind-ar-js-doc')) ||
                        href.includes('.mind') ||
                        href.startsWith('blob:') ||
                        el.getAttribute('download') !== null
                    );
                });
                
                if (downloadButtons.length > 0) {
                    const btn = downloadButtons[0];
                    const href = btn.getAttribute('href');
                    // Double-check it's not a navigation link
                    if (href && !href.startsWith('/mind-ar-js-doc') && (href.startsWith('blob:') || href.includes('.mind') || btn.getAttribute('download'))) {
                        return {
                            href: href,
                            download: btn.getAttribute('download') || 'target.mind',
                            selector: btn.tagName.toLowerCase(),
                            text: btn.textContent
                        };
                    }
                }
                
                // PRIORITY 3: Check window object for compiled data
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
            console.error(`📥 Download link found: ${downloadInfo.href.substring(0, 80)}...`);
            console.error(`   Download attribute: ${downloadInfo.download || 'none'}`);
            console.error(`   Selector: ${downloadInfo.selector || 'unknown'}`);
            
            // CRITICAL: Only use blob URLs - they're the actual compiled files
            // Relative URLs like "/mind-ar-js-doc/..." are navigation links, not downloads
            if (downloadInfo.href.startsWith('blob:')) {
                // Handle blob URL - get the data via page evaluation
                console.error('📦 Extracting data from blob URL...');
                console.error(`   Blob URL: ${downloadInfo.href.substring(0, 60)}...`);
                
                let buffer = null;
                let attempts = 0;
                const maxBlobAttempts = 5;
                
                // Try multiple times to fetch the blob (sometimes it needs a moment)
                while (!buffer && attempts < maxBlobAttempts) {
                    try {
                        buffer = await page.evaluate(async (blobUrl) => {
                            try {
                                const response = await fetch(blobUrl);
                                if (!response.ok) {
                                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                }
                                const blob = await response.blob();
                                if (blob.size === 0) {
                                    throw new Error('Blob is empty');
                                }
                                const arrayBuffer = await blob.arrayBuffer();
                                return Array.from(new Uint8Array(arrayBuffer));
                            } catch (error) {
                                console.error('Error fetching blob:', error.message);
                                return null;
                            }
                        }, downloadInfo.href);
                        
                        if (buffer && buffer.length > 0) {
                            break;
                        }
                    } catch (error) {
                        console.error(`⚠️  Blob fetch attempt ${attempts + 1} failed:`, error.message);
                    }
                    
                    if (!buffer) {
                        attempts++;
                        if (attempts < maxBlobAttempts) {
                            console.error(`   Retrying blob fetch (attempt ${attempts + 1}/${maxBlobAttempts})...`);
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                    }
                }
                
                if (buffer && buffer.length > 0) {
                    // Verify it's a valid .mind file (should be reasonable size)
                    // .mind files are typically at least a few KB (compressed binary format)
                    const minSize = 500; // Minimum reasonable size for a .mind file
                    if (buffer.length < minSize) {
                        console.error(`⚠️  Warning: Downloaded file is very small (${buffer.length} bytes). Expected at least ${minSize} bytes for a .mind file.`);
                        console.error(`   This might indicate the file is incomplete or corrupted.`);
                        // Still try to save it, but warn the user
                    } else {
                        console.error(`   File size looks good: ${buffer.length} bytes`);
                    }
                    
                    // Write the file
                    console.error(`   Writing file to: ${outputPath}...`);
                    fs.writeFileSync(outputPath, Buffer.from(buffer));
                    const fileSize = fs.statSync(outputPath).size;
                    
                    // Verify file was written correctly
                    if (fileSize !== buffer.length) {
                        throw new Error(`File size mismatch: wrote ${fileSize} bytes but expected ${buffer.length}`);
                    }
                    
                    // Additional verification: check if file is readable and has content
                    const verifyBuffer = fs.readFileSync(outputPath);
                    if (verifyBuffer.length !== buffer.length) {
                        throw new Error(`File verification failed: re-read file size (${verifyBuffer.length}) doesn't match written size (${buffer.length})`);
                    }
                    
                    // Check file header to ensure it's a valid binary file (not HTML error page)
                    const fileHeader = verifyBuffer.slice(0, 10);
                    const isLikelyBinary = fileHeader.some(byte => byte < 32 && byte !== 9 && byte !== 10 && byte !== 13);
                    if (!isLikelyBinary && verifyBuffer.length > 100) {
                        // If it's all ASCII and large, might be an HTML error page
                        const textStart = verifyBuffer.slice(0, 200).toString('utf-8');
                        if (textStart.includes('<html') || textStart.includes('<!DOCTYPE')) {
                            throw new Error('Downloaded file appears to be an HTML error page, not a .mind file');
                        }
                    }
                    
                    console.error(`✅ Compilation successful! Output: ${path.basename(outputPath)} (${(fileSize / 1024).toFixed(2)} KB)`);
                    console.error(`   File verified: ${fileSize} bytes written and verified`);
                    console.log('SUCCESS');
                    process.exit(0);
                } else {
                    throw new Error(`Failed to extract data from blob URL after ${maxBlobAttempts} attempts. The blob may have expired or the download link may be invalid.`);
                }
            } else {
                // Non-blob URL - likely a navigation link, not a download
                // Wait a bit more and try to find the actual blob URL
                console.error('⚠️  Download link is not a blob URL, waiting for actual download link...');
                console.error(`   Found link: ${downloadInfo.href} (this might be a navigation link)`);
                
                // Wait a bit more for the blob URL to appear
                let blobFound = false;
                for (let waitAttempt = 0; waitAttempt < 20; waitAttempt++) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    const blobCheck = await page.evaluate(() => {
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {
                            const href = el.getAttribute('href');
                            if (href && href.startsWith('blob:')) {
                                return {
                                    href: href,
                                    download: el.getAttribute('download') || 'target.mind'
                                };
                            }
                        }
                        return null;
                    });
                    
                    if (blobCheck && blobCheck.href) {
                        console.error(`✅ Found blob URL after waiting: ${blobCheck.href.substring(0, 60)}...`);
                        downloadInfo = blobCheck;
                        blobFound = true;
                        break;
                    }
                }
                
                if (!blobFound) {
                    throw new Error('Compilation may have completed but no blob URL found. The download link might be a navigation link, not the actual file.');
                }
                
                // Now handle as blob URL
                if (downloadInfo.href.startsWith('blob:')) {
                    // Extract blob data
                    console.error('📦 Extracting data from blob URL (after wait)...');
                    const buffer = await page.evaluate(async (blobUrl) => {
                        try {
                            const response = await fetch(blobUrl);
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                            }
                            const blob = await response.blob();
                            if (blob.size === 0) {
                                throw new Error('Blob is empty');
                            }
                            const arrayBuffer = await blob.arrayBuffer();
                            return Array.from(new Uint8Array(arrayBuffer));
                        } catch (error) {
                            console.error('Error fetching blob:', error.message);
                            return null;
                        }
                    }, downloadInfo.href);
                    
                    if (buffer && buffer.length > 0) {
                        // Verify and save
                        const minSize = 500;
                        if (buffer.length < minSize) {
                            console.error(`⚠️  Warning: File is very small (${buffer.length} bytes)`);
                        }
                        
                        fs.writeFileSync(outputPath, Buffer.from(buffer));
                        const fileSize = fs.statSync(outputPath).size;
                        
                        // Verify it's not HTML
                        const verifyBuffer = fs.readFileSync(outputPath);
                        const textStart = verifyBuffer.slice(0, 200).toString('utf-8');
                        if (textStart.includes('<html') || textStart.includes('<!DOCTYPE')) {
                            throw new Error('Downloaded file appears to be an HTML error page, not a .mind file');
                        }
                        
                        console.error(`✅ Compilation successful! Output: ${path.basename(outputPath)} (${(fileSize / 1024).toFixed(2)} KB)`);
                        console.log('SUCCESS');
                        process.exit(0);
                    } else {
                        throw new Error('Failed to extract data from blob URL after waiting');
                    }
                } else {
                    throw new Error('Download link is not a blob URL and no blob URL was found after waiting');
                }
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
