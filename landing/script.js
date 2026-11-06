// address of my server, I will change this after the server is deployed
const API_URL = "https://YOUR-API-NAME.onrender.com";

const statusLine = document.getElementById("status");
const rows = document.getElementById("rows");

// puts the top 10 entries into the table
function showRows(entries) {
  if (!Array.isArray(entries) || entries.length === 0) {
    statusLine.textContent = "No scores yet. Be the first.";
    return;
  }
  statusLine.textContent = "";
  for (const entry of entries) {
    const row = document.createElement("tr");
    for (const value of [entry.rank, entry.player_name, entry.score]) {
      const cell = document.createElement("td");
      // textContent never runs html, so a strange player name cannot break the page
      cell.textContent = String(value);
      row.appendChild(cell);
    }
    rows.appendChild(row);
  }
}

// the free server sleeps when nobody uses it, so the first load can take about a minute
async function loadLeaderboard() {
  statusLine.textContent =
    "Waking up the server, this can take up to a minute...";
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(API_URL + "/leaderboard?limit=10", {
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error("bad status");
    }
    const data = await response.json();
    showRows(data.entries);
  } catch (error) {
    statusLine.textContent =
      "The leaderboard is not available right now. Reload the page to try again.";
  } finally {
    clearTimeout(timer);
  }
}

loadLeaderboard();
