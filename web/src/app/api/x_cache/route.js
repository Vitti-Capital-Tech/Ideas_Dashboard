import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const requestedDate = searchParams.get('date');

  // Today's date in YYYY-MM-DD (Sydney time is handled by get_today_str in python, but let's align it)
  // Sydney is UTC+10 (AEST) or UTC+11 (AEDT). Let's use simple timezone offset or standard Date.
  // The python script creates files using SYDNEY_TZ. So let's write dates in the local timezone (Sydney)
  // to find matching files.
  const now = new Date();
  // Simple offset adjustment for Sydney (UTC+10 by default)
  const sydneyOffset = 10 * 60; // in minutes
  const localTime = now.getTime();
  const localOffset = now.getTimezoneOffset(); // in minutes
  const sydneyTime = new Date(localTime + (sydneyOffset + localOffset) * 60000);
  const todayStr = `${sydneyTime.getFullYear()}-${String(sydneyTime.getMonth() + 1).padStart(2, '0')}-${String(sydneyTime.getDate()).padStart(2, '0')}`;

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
      const files = fs.readdirSync(logsDir).filter(f => f.startsWith('x_') && f.endsWith('.json'));
      files.forEach(f => {
        const match = f.match(/^x_(\d{4}-\d{2}-\d{2})/);
        if (match) dates.add(match[1]);
      });
      // Sort descending; today is always first even if no log file yet
      const sorted = Array.from(dates).sort().reverse();
      if (!sorted.includes(todayStr)) sorted.unshift(todayStr);
      return sorted;
    } catch (e) {
      console.error('Error getting X dates:', e);
      return [todayStr];
    }
  };

  const getLogForDate = (date) => {
    try {
      if (!date || !fs.existsSync(logsDir)) return null;
      const filePath = path.join(logsDir, `x_${date}.json`);
      if (!fs.existsSync(filePath)) return null;
      const raw = fs.readFileSync(filePath, 'utf-8').trim();
      if (!raw) return null;
      return JSON.parse(raw); // Returns array of {timestamp, type, content}
    } catch (e) {
      console.error(`Error reading X log for ${date}:`, e.message);
      return null;
    }
  };

  const availableDates = getAvailableDates();
  const dateToFetch = requestedDate || todayStr;

  const entries = getLogForDate(dateToFetch);

  // If today has no log, also send the most recent past entries so the UI
  // can show them as a fallback
  let previousEntries = null;
  let previousDate = null;
  if (!entries && dateToFetch === todayStr) {
    const pastDates = availableDates.filter(d => d !== todayStr);
    if (pastDates.length > 0) {
      previousDate = pastDates[0];
      previousEntries = getLogForDate(previousDate);
    }
  }

  return NextResponse.json({
    entries,
    previousEntries,
    previousDate,
    availableDates,
    selectedDate: dateToFetch,
    todayStr,
  });
}
