#!/usr/bin/env node
/**
 * Test: DeepSeek-OCR vs PaddleOCR
 * Usage: node test_deepseek_ocr.js <image_path>
 */

import ollama from 'ollama'
import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

const imagePath = process.argv[2] || './images/Screenshot 2026-03-13 at 14.04.03.png'

if (!fs.existsSync(imagePath)) {
  console.error(`Image not found: ${imagePath}`)
  process.exit(1)
}

const imageBuffer = fs.readFileSync(imagePath)
const base64 = imageBuffer.toString('base64')

console.log(`\n=== Testing: ${path.basename(imagePath)} ===\n`)

// --- DeepSeek-OCR ---
console.log('--- DeepSeek-OCR ---')
const t1 = Date.now()
const response = await ollama.chat({
  model: 'deepseek-ocr',
  messages: [{
    role: 'user',
    content: 'Extract the text in the image',
    images: [base64],
  }],
})
const t2 = Date.now()
console.log(response.message.content)
console.log(`\n[DeepSeek-OCR took ${((t2 - t1) / 1000).toFixed(1)}s]\n`)
