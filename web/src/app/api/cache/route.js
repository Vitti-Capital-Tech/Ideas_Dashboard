import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const requestedDate = searchParams.get('date');

  // Today's date in YYYY-MM-DD
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

  // Smart resolution for logs directory
  const getLogsPath = () => {
    const possiblePaths = [
      path.join(process.cwd(), 'logs'),        // Running from /web (Vercel)
      path.join(process.cwd(), 'web', 'logs'), // Running from repo root
    ];
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) return p;
    }
    return possiblePaths[0];
  };

  const logsDir = getLogsPath();

  const getAvailableDates = () => {
    try {
      if (!fs.existsSync(logsDir)) return [];
      const dates = new Set();
      const rootFiles = fs.readdirSync(logsDir).filter(f => f.endsWith('.json'));
      rootFiles.forEach(f => {
        const match = f.match(/^(\d{4}-\d{2}-\d{2})/);
        if (match) dates.add(match[1]);
      });
      // Sort descending; today is always first even if no log file yet
      const sorted = Array.from(dates).sort().reverse();
      if (!sorted.includes(todayStr)) sorted.unshift(todayStr);
      return sorted;
    } catch (e) {
      console.error('Error getting dates:', e);
      return [todayStr];
    }
  };

  const getLogForDate = (date) => {
    try {
      if (!date || !fs.existsSync(logsDir)) return null;
      const filePath = path.join(logsDir, `${date}.json`);
      if (!fs.existsSync(filePath)) return null;
      const raw = fs.readFileSync(filePath, 'utf-8').trim();
      if (!raw) return null;
      const parsedArray = JSON.parse(raw);
      return Array.isArray(parsedArray) && parsedArray.length > 0
        ? parsedArray[parsedArray.length - 1]
        : null;
    } catch (e) {
      console.error(`Error reading log for ${date}:`, e.message);
      return null;
    }
  };

  const availableDates = getAvailableDates();
  const dateToFetch = requestedDate || todayStr;

  const ideas = getLogForDate(dateToFetch);

  // If today has no log, also send the most recent past ideas so the UI
  // can show them as a "meanwhile" fallback below the pending banner
  let previousIdeas = null;
  let previousDate = null;
  if (!ideas && dateToFetch === todayStr) {
    const pastDates = availableDates.filter(d => d !== todayStr);
    if (pastDates.length > 0) {
      previousDate = pastDates[0];
      previousIdeas = getLogForDate(previousDate);
    }
  }

  return NextResponse.json({
    ideas,
    previousIdeas,   // most recent past ideas when today has no log
    previousDate,    // date those past ideas are from
    availableDates,
    selectedDate: dateToFetch,
    todayStr,
  });
}
