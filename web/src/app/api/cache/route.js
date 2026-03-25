import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

export async function GET() {
  const logsDir = path.join(process.cwd(), '..', 'logs');
  
  const getLatestLogItem = (type) => {
    try {
      if (!fs.existsSync(logsDir)) return null;
      // Get all JSON files for the specific type
      const files = fs.readdirSync(logsDir)
                      .filter(f => f.endsWith(`-${type}.json`))
                      .sort()
                      .reverse(); // Last Date file first
                      
      if (files.length > 0) {
        const data = fs.readFileSync(path.join(logsDir, files[0]), 'utf-8');
        const parsedArray = JSON.parse(data);
        if (Array.isArray(parsedArray) && parsedArray.length > 0) {
           // Return the most recent run object in the file
           return parsedArray[parsedArray.length - 1]; 
        }
      }
    } catch (e) {
      console.error(`Error reading cache for ${type}:`, e);
    }
    return null;
  };

  return NextResponse.json({
    ceo: getLatestLogItem('ceo'),
    raindrop: getLatestLogItem('raindrop')
  });
}
