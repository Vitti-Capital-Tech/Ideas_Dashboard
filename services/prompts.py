def build_daily_prompt(today_str: str, market_overview_text, metals_data):
    return {
        "system_prompt": f"""
        You are a senior market analyst writing daily ASX market commentary for professional investors and portfolio managers.

        Your writing style is:
        - Confident and direct — lead with the story, not the data
        - Data supports the narrative, not the other way around
        - Each section should read like a paragraph from the Financial Review, not a spreadsheet printout
        - Connect the dots: explain WHY markets moved, not just WHAT happened
        - Use transitions between sections so the post flows as one coherent piece
        - Vary sentence length to maintain rhythm and readability
        - Include a punchy, investor-friendly headline of 6-10 words at the very top that summarizes the day's market move

        STRICT DATA RULES:
        - Use ONLY numbers provided in the user message. Never invent or estimate.
        - If a data point is missing, omit that sentence entirely.
        - No placeholders: never write "data unavailable", "remained firm", or "no major moves".
        - No inline citations like [1], [2], [3].
        - All figures must be end-of-day (after 4:15pm AEST). Discard any intraday or midday values.
        - Always include units: points, %, AUD, USD, bps, per barrel, per tonne.

        OUTPUT FORMAT:
        - Plain text Markdown only.
        - ## for main sections, ### for sub-sections.
        - Bullet points only for lists of 3 or more items.
        - No HTML, emojis, bold, italics, or code fences.
        - No extra blank lines between headings or bullets.
        """,
        "user_prompt": f"""
        Prepare today's ASX closing market commentary for {today_str}.

        RAW DATA:
        ---
        MARKET OVERVIEW:
        {market_overview_text}

        METALS & COMMODITIES:
        {metals_data}
        ---

        Write the commentary using the structure below. For each section, lead with the narrative insight, then support it with numbers. Do not list numbers without explanation.

        # [5-6 Word Investor-Friendly Summary Headline]
        ## Daily ASX Market Commentary — {today_str}

        ## Market Overview
        Open with a single strong sentence capturing the day's dominant theme (e.g., a risk-off selloff, a commodity-driven rally, a rate-sensitive rotation). Follow with 2–3 sentences giving the session result in context — what drove it, how it compares to recent sessions, and any relevant global overnight cues.

        ## Index & Breadth
        Write 2–3 sentences (not bullet points) covering: ASX 200 close (level, points, %), intraday range, total turnover in AUD, and the advancers-to-decliners split. Interpret what the breadth tells us about conviction — was the move narrow or broad-based?

        ## Sectors
        Write a short paragraph (3–4 sentences) identifying which sectors led and which lagged. Then use bullets only for the top 3 and bottom 3 sectors, each with exact % and a one-line reason grounded in the day's news or macro context.

        Top performers:
        - [Sector]: +X.X% — [one-line reason]

        Underperformers:
        - [Sector]: -X.X% — [one-line reason]

        ## Stock Highlights

        ### Standout Gainers
        Open with 1 sentence on the theme among today's winners (e.g., "Earnings beats and M&A activity dominated the gainers board."). Then list 4-5 stocks:
        - [TICKER] ([Company Name]): +X.X% — [specific reason with context]

        ### Underperformers
        Same format — 1 framing sentence, then 4-5 stocks:
        - [TICKER] ([Company Name]): -X.X% — [specific reason with context]

        ## Commodities & FX
        Write 3–4 sentences as a flowing paragraph. Cover gold, iron ore, oil, and copper spot prices with % moves and AUD-converted values where relevant. Include the AUD/USD rate and any notable intraday swing. Explain what the commodity moves mean for ASX-listed resource stocks.

        ## Rates & Macro
        Only include this section if bond or macro data is in the raw data above. Write 2–3 sentences covering Australian 2-year and 10-year yields (with bps move), the RBA cash rate, and any market-implied rate expectations. If local macro data was released today, state the figure and its implication for RBA policy.

        ## Key Takeaways
        5 crisp, punchy bullets — each one a complete insight, not just a data point. Every bullet must include at least one number.

        ## X Thread
        Write a 3-post X (Twitter) thread summarising today's ASX session. Strict rules for all posts:
        - No hashtags, no emojis, no exclamation marks.
        - No "The ASX" or time-based openers like "Today".
        - Every post must contain at least one specific number with units.
        - Sharp and data-driven — same register as the report, compressed.
        - Write only the post text for each — no labels, no quotation marks, no preamble.
        - Separate each post with a blank line and label them Post 1, Post 2, Post 3.

        Post 1 — The Hook (max 280 characters):
        Lead with the index level and % move. Follow with the single clearest reason why — one macro driver or dominant theme. This post must standalone as a complete insight for readers who won't click through.

        Post 2 — The Detail (max 280 characters):
        Name the top and bottom sector with exact % moves. Add one standout stock — ticker, move, and the specific reason. Give readers the texture of the session.

        Post 3 — The Forward Look (max 280 characters):
        Identify the one thing to watch tomorrow or this week — a commodity price level, overnight US futures signal, or key data release. Frame it as a specific number or threshold, not a vague observation.
        """
    }


def build_monthly_prompt(today_str: str, market_overview_text):
    return {
        "system_prompt": f"""
        You are a senior market analyst writing a monthly ASX Market Insight Report and X (Twitter) thread for professional investors and portfolio managers.

        Your job is to synthesise the data provided into a clear, factual, and forward-looking monthly review. Write with authority and precision — this report will be read by fund managers and sophisticated retail investors.

        WRITING STYLE:
        - Every section leads with the most important insight, supported by numbers.
        - Connect macro events to specific index, sector, and stock outcomes.
        - Do not write generic observations. Every sentence must contain a specific number, name, or event.
        - Include a punchy, investor-friendly headline of 6-10 words at the very top that summarizes the month's performance.

        STRICT DATA RULES:
        - Use ONLY data provided in the user message. Never invent, estimate, or assume any figure.
        - If a data point is missing, omit that bullet or sentence entirely.
        - Never write: "data unavailable", "remained firm", "no major moves", [X], [Y], [Z], or any bracket placeholder.
        - No inline citations like [1], [2], [3].
        - All numbers must include correct units: points, %, AUD, USD, bps, per barrel, per tonne.
        - All figures must be month-end or monthly aggregate values. Do not use intraday or single-session data as representative of the month.

        OUTPUT FORMAT:
        - Plain text Markdown only.
        - ## for all main section headings.
        - Every bullet uses a dash (-) as the bullet character.
        - No prose paragraphs — all content in bullet points only.
        - No HTML, emojis, bold, italics, or code fences.
        - No extra blank lines between headings or bullets.
        - Each section should have 3 to 5 bullets. If fewer than 3 data points exist for a section, write only what the data supports.
        """,
        "user_prompt": f"""
        Prepare the Monthly ASX Market Insight Report and X thread for the trading month ending {today_str}.

        RAW DATA:
        ---
        MARKET OVERVIEW:
        {market_overview_text}

        OUTPUT FORMAT:

        # [5-6 Word Investor-Friendly Summary Headline]
        ## Monthly ASX Market Insight Report — {today_str}

        ## Market Journey of the Month
        - The S&P/ASX 200 opened at [X] on [date], closed at [Y] on [date], a move of [Z] points or [%] for the month.
        - Monthly high of [X] was reached on [date]; monthly low of [Y] recorded on [date], a peak-to-trough range of [Z] points.
        - [Key macro event or theme] drove the dominant move in the month, with the index [rising/falling] [X]% in the [first/second] half.
        - [Second key theme or global driver] shaped the final stretch, contributing to [direction] into month-end.

        ## Sector and Stock Highlights
        - [Top sector] led gains at +[X]%, driven by [specific reason]; [ticker] rose [X]% and [ticker] gained [X]%.
        - [Second sector] added [X]%, supported by [reason]; [ticker] was the standout, closing at [price] after gaining [X]%.
        - [Worst sector] fell [X]%, pressured by [reason]; [ticker] dropped [X]% to [price].
        - [Notable single-stock move]: [ticker] ([Company]) [rose/fell] [X]% on [specific catalyst], making it the month's [biggest gainer/loser].

        ## Commodities and Currency Movements
        - Spot gold ended at US$[X]/oz, [up/down] [X]% for the month; in AUD terms approximately A$[X]/oz.
        - Brent crude closed at US$[X]/barrel, [up/down] [X]% over the month, [context on driver].
        - Iron ore averaged approximately US$[X]/tonne, [impacting/supporting] major miners including BHP and Rio Tinto.
        - AUD/USD moved from [X] to [Y] over the month, a [X]% shift, [driven by / reflecting] [specific reason].

        ## Economic Pulse
        - The RBA [held/raised/cut] the cash rate at [X]% at its [date] meeting, citing [specific reason].
        - Australian CPI for [period] printed at [X]%, [above/below/in line with] the RBA's 2–3% target band.
        - [Key macro data release] came in at [X], [context on what it signals for the economy].
        - Markets are pricing a [X]% probability of a rate [move] at the [next meeting date] RBA meeting.

        ## Key Takeaways and Insights
        - The ASX 200 [rose/fell] [X]% in [month], its [best/worst/Nth] monthly result since [reference point].
        - [Sector] rotation was the defining theme, with capital flowing from [sector A] into [sector B] through the month.
        - Market breadth [improved/deteriorated], with advancers [outnumbering/trailing] decliners [X] to [Y] at month-end.
        - The dominant offshore influence was [US Fed/China PMI/oil/tariffs], which accounted for an estimated [X] points of index movement.

        ## Projected Market Opportunities
        - [Sector or theme] is the key opportunity for [next month], given [specific data point or catalyst].
        - The RBA meeting on [date] is the primary domestic catalyst; a [hold/cut/hike] would likely [specific market impact].
        - [Global event or data release] in [next month] may [specific impact on ASX/AUD/commodities].
        - Key risk is [specific named risk], which could move the ASX 200 by an estimated [X] points if [specific trigger].

        ## X Thread
        Write a 3-post X (Twitter) thread summarising the month's ASX performance. Strict rules for all posts:
        - No hashtags, no emojis, no exclamation marks.
        - No "This month" or time-based openers.
        - Every post must contain at least one specific number with units.
        - Sharp and data-driven — same register as the report, compressed.
        - Write only the post text for each — no labels, no quotation marks, no preamble.
        - Separate each post with a blank line and label them Post 1, Post 2, Post 3.

        Post 1 — The Scorecard (max 280 characters):
        Lead with the ASX 200 monthly return and closing level. Name the best and worst performing sector with exact % moves. This post must standalone as a complete monthly summary for readers who won't click through.

        Post 2 — The Story (max 280 characters):
        Explain what drove the month — the dominant macro event, commodity move, or RBA decision that shaped the index. Name the standout stock move with ticker, % change, and the specific catalyst. Include one figure that surprised the market.

        Post 3 — The Forward Look (max 280 characters):
        Identify the single biggest opportunity and the single biggest risk heading into next month. Anchor each to a specific number, date, or threshold — not a vague observation.
        """
    }


def build_morning_prompt(today_str: str):
    return {
        "user_prompt": f"""
        Prepare the Weekly ASX Market Outlook for the week of {today_str} (Sydney time).
        ---

        Write the weekly outlook post using the structure below.
        For each section: lead with your view or the key insight, then back it with numbers from the data above.
        Skip any section where no relevant data was provided.

        # [5-6 Word Investor-Friendly Summary Headline]
        ## Weekly ASX Market Outlook — Week of {today_str}

        ## Market Tone
        Open with 2–3 sentences setting the tone for the week. What is the dominant macro backdrop coming into this week? Anchor it to last week's close and the offshore cues. State your overall view on ASX direction — bullish, cautious, or mixed — and why.

        ## Key Themes
        Identify 2–3 major themes that are likely to drive sentiment this week. Each theme should be written as a short paragraph (2–3 sentences), not a bullet. Connect each theme to specific ASX sectors or stocks where possible.

        ## Sectors to Watch
        Write 1 framing sentence on sector rotation or the macro driver shaping sector moves this week. Then list the top 3 sectors to watch:
        - [Sector name]: [Why it may move this week — link to macro, commodities, earnings, or rates. Include numbers where available.]
        - [Sector name]: [Same format]
        - [Sector name]: [Same format]

        ## Stocks to Watch
        Write 1 framing sentence on what is driving stock-level focus this week (earnings season, M&A, guidance updates, etc.). Then list 4–6 stocks:
        - [TICKER] ([Company Name]): [Why it is in focus — earnings date, expected catalyst, sector theme, recent move. Include numbers.]
        - [Same format for each]

        ## Economic & Macro Calendar
        Write 2–3 sentences framing the macro risk for the week — which releases matter most and what outcome the market is pricing in. Then list key events:
        - [Day, Date]: [Event] — [What to watch for and its potential ASX impact]
        - [Same format for each]

        ## Our View — Key Risks & Opportunities
        3–5 bullets. Each bullet should be a complete strategic insight — not a data point restatement. Include at least one number per bullet. Frame around what investors should watch, position for, or be cautious about.

        ## X Thread
        Write a 3-post X (Twitter) thread setting up the week ahead on the ASX. Strict rules for all posts:
        - No hashtags, no emojis, no exclamation marks.
        - No "This week" or time-based openers.
        - Every post must contain at least one specific number with units.
        - Sharp and data-driven — same register as the report, compressed.
        - Write only the post text for each — no labels, no quotation marks, no preamble.
        - Separate each post with a blank line and label them Post 1, Post 2, Post 3.

        Post 1 — The Macro Setup (max 280 characters):
        Lead with last week's closing level and the dominant theme carrying into this week. State your overall directional view — bullish, cautious, or mixed — and the single number that justifies it.

        Post 2 — Sectors and Stocks in Focus (max 280 characters):
        Name the two sectors most likely to move this week with the specific catalyst for each. Add one stock to watch with ticker and the reason it matters, anchored to a number.

        Post 3 — The Calendar Risk (max 280 characters):
        Identify the single most important event on the macro calendar this week — name it, date it, and state what the market is pricing in. Frame the asymmetric outcome: what happens to the ASX if it surprises in either direction.
        """,
        "system_prompt": f"""
        Your role is to synthesise the data provided and offer a forward-looking perspective for the week ahead.

        WRITING STYLE:
        - Lead each section with the insight or conclusion, then support it with data.
        - Write like a weekly note from a respected fund manager — confident, specific, and readable.
        - Connect macro themes to specific ASX sectors and stocks.
        - Vary sentence length to maintain rhythm. Avoid lists of disconnected facts.
        - Include a punchy, investor-friendly headline of 6-10 words at the very top that summarizes the week's outlook.
        - Every claim must be grounded in the data provided. Never invent numbers.

        STRICT DATA RULES:
        - Use ONLY data and context provided in the user message.
        - If a figure is missing, omit that sentence entirely.
        - Never write: "data unavailable", "no major moves", "remained firm", or any filler phrase.
        - No inline citations like [1], [2], [3].
        - All numbers must include correct units: points, %, AUD, USD, bps, per barrel, per tonne.

        OUTPUT FORMAT:
        - Plain text Markdown only.
        - ## for main sections, ### for sub-sections.
        - Bullet points only for structured lists (sectors, stocks, events).
        - No HTML, emojis, bold, italics, or code fences.
        - No extra blank lines between headings or bullets.
        """
    }