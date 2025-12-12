/**
 * MindAR Target Image Compiler Script
 * Compiles a single image to .mind file using MindAR Core API
 * 
 * Reference: https://hiukim.github.io/mind-ar-js-doc/core-api
 * Web Compiler: https://hiukim.github.io/mind-ar-js-doc/tools/compile
 * 
 * Usage: node compile_target.js <input_image> <output.mind>
 */

const fs = require('fs');
const path = require('path');
const { Compiler } = require('mind-ar');

async function compileImage(inputPath, outputPath) {
    try {
        // Read image file
        const imageBuffer = fs.readFileSync(inputPath);
        const imageBase64 = imageBuffer.toString('base64');
        const ext = path.extname(inputPath).toLowerCase();
        const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
        
        // Create a data URL for the image
        const dataUrl = `data:${mimeType};base64,${imageBase64}`;
        
        // For Node.js, we need to create an image-like object
        // MindAR's Compiler expects HTMLImageElement, but we can work around this
        // by using the image data directly
        
        // Initialize compiler
        const compiler = new Compiler();
        
        // Create a simple image wrapper that mimics HTMLImageElement
        // The compiler needs width, height, and src properties
        const image = {
            src: dataUrl,
            width: 0,
            height: 0,
            complete: false,
            onload: null,
            onerror: null
        };
        
        // Load image dimensions using a simple approach
        // For production, you might want to use 'sharp' or 'canvas' package
        // For now, we'll try to get dimensions from the image data
        const { createCanvas, loadImage } = require('canvas');
        
        try {
            // Try using canvas to load the image properly
            const canvasImage = await loadImage(dataUrl);
            image.width = canvasImage.width;
            image.height = canvasImage.height;
            image.complete = true;
            
            // Compile the image
            const dataList = await compiler.compileImageTargets([canvasImage], (progress) => {
                process.stdout.write(`Progress: ${progress}%\n`);
            });
            
            // Export to buffer
            const exportedBuffer = await compiler.exportData();
            
            // Write to file
            fs.writeFileSync(outputPath, exportedBuffer);
            
            console.log('SUCCESS');
            process.exit(0);
        } catch (canvasError) {
            // Fallback: If canvas is not available, try without it
            console.warn('Canvas not available, trying alternative method...');
            
            // Alternative: Use the image data URL directly
            // This might work if MindAR can handle data URLs
            const dataList = await compiler.compileImageTargets([image], (progress) => {
                process.stdout.write(`Progress: ${progress}%\n`);
            });
            
            const exportedBuffer = await compiler.exportData();
            fs.writeFileSync(outputPath, exportedBuffer);
            
            console.log('SUCCESS');
            process.exit(0);
        }
    } catch (error) {
        console.error('ERROR:', error.message);
        if (error.stack) {
            console.error(error.stack);
        }
        process.exit(1);
    }
}

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
    console.error('Usage: node compile_target.js <input_image> <output.mind>');
    console.error('');
    console.error('This script uses MindAR Core API to compile images to .mind files.');
    console.error('Reference: https://hiukim.github.io/mind-ar-js-doc/core-api');
    process.exit(1);
}

if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found: ${inputPath}`);
    process.exit(1);
}

compileImage(inputPath, outputPath);

