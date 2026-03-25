import { NextResponse } from 'next/server';

export async function POST(req) {
  try {
    const GITHUB_PAT = process.env.GITHUB_PAT;
    const GITHUB_REPO = process.env.GITHUB_REPO; // format: "username/repo"
    
    if (!GITHUB_PAT || !GITHUB_REPO) {
      return NextResponse.json({ 
        error: "Missing GITHUB_PAT or GITHUB_REPO in your .env.local file. You must add these to trigger GitHub Actions." 
      }, { status: 400 });
    }

    const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/generate.yml/dispatches`, {
      method: "POST",
      headers: {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": `token ${GITHUB_PAT}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error("GitHub Action Error:", errText);
      throw new Error(`GitHub API Error: Check if PAT has 'repo' access or if repository name is correct.`);
    }

    return NextResponse.json({ success: true, message: "Workflow triggered successfully!" });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
