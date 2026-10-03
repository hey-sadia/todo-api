
# Bonus: My Scraper vs AI Scraper

I gave the same task to an AI and compared its result with mine.
The AI code is in `bonus/ai_main.py`.

| | My scraper | AI scraper |
|---|---|---|
| Valid books | 60 | 59 |
| Errors | 0 | 1 |
| Run time (first run) | not measured | 106 seconds |
| Cache file names | short slug from the URL | full URL turned into a file name |
| Delay between requests | 0.5 seconds | 1 second |
| Output folder | `output/` | current folder |

## What the AI got wrong

One book has a very long title. The AI made the cache file name from the whole URL, so the name was too long for Windows and the file could not be saved. That book ended up in `errors.json` and was lost.

## What the AI did well

- It did not crash. It logged the error and kept going.
- It stored the star rating as a number (1 to 5).
- It used proper logging with timestamps.

## What I learned

AI code can look correct and still fail on real data. I only found the long-name bug by running it and reading `errors.json`. Running and checking the output is more important than trusting the code.