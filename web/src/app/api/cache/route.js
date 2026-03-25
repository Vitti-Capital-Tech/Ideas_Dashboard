import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const requestedDate = searchParams.get('date');
  
  // Smart resolution for logs directory
  const getLogsPath = () => {
    const possiblePaths = [
      path.join(process.cwd(), 'logs'),          // If running from /web (Vercel default)
      path.join(process.cwd(), 'web', 'logs'),   // If running from repo root
    ];
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) return p;
    }
    return possiblePaths[0]; // fallback
  };

  const logsDir = getLogsPath();
  console.log('--- API: Reading logs from:', logsDir);
  console.log('--- API: Requested date:', requestedDate);
  const getAvailableDates = () => {
    try {
      if (!fs.existsSync(logsDir)) return [];
      const folders = ['ceo', 'posts', 'ideas'];
      const dates = new Set();
      
      folders.forEach(folder => {
        const folderPath = path.join(logsDir, folder);
        if (fs.existsSync(folderPath)) {
          const files = fs.readdirSync(folderPath).filter(f => f.endsWith('.json'));
          files.forEach(f => {
            const match = f.match(/^(\d{4}-\d{2}-\d{2})/);
            if (match) dates.add(match[1]);
          });
        }
      });

      // Also check root for legacy files
      const rootFiles = fs.readdirSync(logsDir).filter(f => f.endsWith('.json'));
      rootFiles.forEach(f => {
        const match = f.match(/^(\d{4}-\d{2}-\d{2})/);
        if (match) dates.add(match[1]);
      });

      return Array.from(dates).sort().reverse();
    } catch (e) {
      console.error('Error getting dates:', e);
      return [];
    }
  };

  const getLogForDate = (type, date) => {
    try {
      if (!fs.existsSync(logsDir)) return null;
      
      // Try subfolder first
      const subDir = path.join(logsDir, type);
      let fileName = date ? `${date}.json` : null;
      
      if (fs.existsSync(subDir)) {
        if (!fileName) {
          const files = fs.readdirSync(subDir).filter(f => f.endsWith('.json')).sort().reverse();
          fileName = files.length > 0 ? files[0] : null;
        }
        if (fileName) {
          const filePath = path.join(subDir, fileName);
          if (fs.existsSync(filePath)) {
            try {
              const raw = fs.readFileSync(filePath, 'utf-8').trim();
              if (!raw) return null;
              const parsedArray = JSON.parse(raw);
              return Array.isArray(parsedArray) && parsedArray.length > 0
                ? parsedArray[parsedArray.length - 1]
                : null;
            } catch (parseErr) {
              console.error(`Failed to parse ${type} log:`, parseErr.message);
              return null;
            }
          }
        }
      }

      // Legacy fallback (root folder)
      const legacyFileName = date ? `${date}-${type}.json` : null;
      const legacyPath = legacyFileName ? path.join(logsDir, legacyFileName) : null;
      if (legacyPath && fs.existsSync(legacyPath)) {
        const data = fs.readFileSync(legacyPath, 'utf-8');
        const parsedArray = JSON.parse(data);
        return Array.isArray(parsedArray) && parsedArray.length > 0 ? parsedArray[parsedArray.length - 1] : null;
      }
    } catch (e) {
      console.error(`Error reading ${type} log:`, e);
    }
    return null;
  };

  const availableDates = getAvailableDates();
  const dateToFetch = requestedDate || (availableDates.length > 0 ? availableDates[0] : null);

  return NextResponse.json({
    ceo: getLogForDate('ceo', dateToFetch),
    ideas: getLogForDate('ideas', dateToFetch),
    posts: getLogForDate('posts', dateToFetch),
    availableDates,
    selectedDate: dateToFetch
  });
}
