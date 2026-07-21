const STORAGE_INFLUENCERS = "ai_influencer_dashboard_influencers_v1";
const STORAGE_POSTS = "ai_influencer_dashboard_posts_v1";

let influencers = [];
let posts = [];

const els = {
  grid: document.getElementById("influencerGrid"),
  search: document.getElementById("search"),
  lineFilter: document.getElementById("lineFilter"),
  cardTemplate: document.getElementById("cardTemplate"),
  createInfluencerForm: document.getElementById("createInfluencerForm"),
  createPostForm: document.getElementById("createPostForm"),
  postInfluencerSelect: document.getElementById("postInfluencerSelect"),
  postList: document.getElementById("postList"),
  statInfluencers: document.getElementById("statInfluencers"),
  statPosts: document.getElementById("statPosts"),
  statLines: document.getElementById("statLines"),
  statLocal: document.getElementById("statLocal"),
  resetDemo: document.getElementById("resetDemo"),
  scrollCreatePost: document.getElementById("scrollCreatePost"),
};

function slugify(value) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function saveInfluencers() {
  localStorage.setItem(STORAGE_INFLUENCERS, JSON.stringify(influencers));
}

function savePosts() {
  localStorage.setItem(STORAGE_POSTS, JSON.stringify(posts));
}

async function loadSeedInfluencers() {
  const stored = localStorage.getItem(STORAGE_INFLUENCERS);
  if (stored) {
    influencers = JSON.parse(stored);
    return;
  }

  const response = await fetch("data/influencers.json");
  const data = await response.json();
  influencers = data.influencers || [];
  saveInfluencers();
}

function loadPosts() {
  posts = JSON.parse(localStorage.getItem(STORAGE_POSTS) || "[]");
}

// Function 1: Create Influencer
function createInfluencer(payload) {
  const personaId = payload.persona_id || slugify(payload.display_name);
  const influencer = {
    persona_id: personaId,
    display_name: payload.display_name,
    age: payload.age || "",
    gender: payload.gender || "",
    demography: payload.demography || "",
    home_base: payload.home_base || "",
    niche: payload.niche,
    line: payload.line || "N",
    approval_state: "draft",
    package_path: `personas/${personaId}`,
    face_reference: payload.face_reference || "",
    contradiction: payload.contradiction || "",
    signature_detail: payload.signature_detail || "",
    source: "local",
  };

  const existingIndex = influencers.findIndex((item) => item.persona_id === personaId);
  if (existingIndex >= 0) {
    influencers[existingIndex] = influencer;
  } else {
    influencers.unshift(influencer);
  }

  saveInfluencers();
  render();
  return influencer;
}

// Function 2: Get all or specific influencers
function getInfluencers(personaId = null) {
  if (personaId) {
    return influencers.find((item) => item.persona_id === personaId) || null;
  }
  return influencers;
}

// Function 3: Create a Post with image and content
function createPost(payload) {
  const influencer = getInfluencers(payload.persona_id);
  const post = {
    post_id: `post-${Date.now()}`,
    persona_id: payload.persona_id,
    display_name: influencer ? influencer.display_name : payload.persona_id,
    platform: payload.platform || "instagram",
    image_path: payload.image_path || (influencer ? influencer.face_reference : ""),
    caption: payload.caption,
    status: "draft",
    continuity: "pending",
    created_at: new Date().toISOString(),
  };
  posts.unshift(post);
  savePosts();
  renderPosts();
  renderStats();
  return post;
}

function renderFilters() {
  const lines = [...new Set(influencers.map((item) => item.line || "N"))].sort();
  els.lineFilter.innerHTML = `<option value="">All lines</option>`;
  for (const line of lines) {
    const option = document.createElement("option");
    option.value = line;
    option.textContent = `Line ${line}`;
    els.lineFilter.appendChild(option);
  }
}

function filteredInfluencers() {
  const query = els.search.value.trim().toLowerCase();
  const line = els.lineFilter.value;
  return influencers.filter((item) => {
    const haystack = `${item.display_name} ${item.niche} ${item.home_base} ${item.demography}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!line || item.line === line);
  });
}

function renderInfluencers() {
  els.grid.innerHTML = "";
  for (const influencer of filteredInfluencers()) {
    const node = els.cardTemplate.content.cloneNode(true);
    const img = node.querySelector(".face");
    img.src = influencer.face_reference || "";
    img.alt = `${influencer.display_name} face reference`;
    img.onerror = () => { img.style.display = "none"; };
    node.querySelector("h4").textContent = influencer.display_name;
    node.querySelector(".badge").textContent = influencer.line || "N";
    node.querySelector(".muted").textContent = `${influencer.age || "?"} - ${influencer.gender || "unknown"} - ${influencer.home_base || "No base"}`;
    node.querySelector(".niche").textContent = influencer.niche || "No niche";
    node.querySelector(".mini").addEventListener("click", () => {
      els.postInfluencerSelect.value = influencer.persona_id;
      document.getElementById("create-post").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    els.grid.appendChild(node);
  }
}

function renderPostInfluencerSelect() {
  els.postInfluencerSelect.innerHTML = "";
  for (const influencer of influencers.slice().sort((a, b) => a.display_name.localeCompare(b.display_name))) {
    const option = document.createElement("option");
    option.value = influencer.persona_id;
    option.textContent = influencer.display_name;
    els.postInfluencerSelect.appendChild(option);
  }
}

function renderPosts() {
  els.postList.innerHTML = "";
  if (!posts.length) {
    els.postList.innerHTML = `<p class="muted">No post drafts yet. Create one from the form above.</p>`;
    return;
  }
  for (const post of posts) {
    const article = document.createElement("article");
    article.className = "post-card";
    article.innerHTML = `
      <img src="${post.image_path || ""}" alt="${post.display_name} post image">
      <div>
        <h4>${post.display_name} - ${post.platform}</h4>
        <p>${post.caption.replace(/\n/g, "<br>")}</p>
        <p class="muted">${post.status} - ${post.continuity} - ${new Date(post.created_at).toLocaleString()}</p>
      </div>
    `;
    els.postList.appendChild(article);
  }
}

function renderStats() {
  els.statInfluencers.textContent = influencers.length;
  els.statPosts.textContent = posts.length;
  els.statLines.textContent = new Set(influencers.map((item) => item.line || "N")).size;
  els.statLocal.textContent = influencers.filter((item) => item.source === "local").length;
}

function render() {
  renderFilters();
  renderInfluencers();
  renderPostInfluencerSelect();
  renderPosts();
  renderStats();
}

els.search.addEventListener("input", renderInfluencers);
els.lineFilter.addEventListener("change", renderInfluencers);

els.createInfluencerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  createInfluencer(Object.fromEntries(form.entries()));
  event.currentTarget.reset();
});

els.createPostForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  createPost(Object.fromEntries(form.entries()));
  event.currentTarget.reset();
});

els.resetDemo.addEventListener("click", async () => {
  localStorage.removeItem(STORAGE_INFLUENCERS);
  localStorage.removeItem(STORAGE_POSTS);
  await loadSeedInfluencers();
  loadPosts();
  render();
});

els.scrollCreatePost.addEventListener("click", () => {
  document.getElementById("create-post").scrollIntoView({ behavior: "smooth", block: "start" });
});

loadSeedInfluencers().then(() => {
  loadPosts();
  render();
});

window.influencerApi = {
  createInfluencer,
  getInfluencers,
  createPost,
};
