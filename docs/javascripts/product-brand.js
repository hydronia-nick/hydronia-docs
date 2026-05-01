const productBrands = [
  {
    key: "riverflow2d",
    match: "/riverflow2d/",
    name: "RiverFlow2D",
    eyebrow: "Hydraulic and Hydrologic Modeling",
    banner: "assets/product-brand/RF2D_top_banner.jpg",
    icon: "assets/product-brand/rf2d_large_icon.png",
    logo: "assets/product-brand/rf2d_logo.png",
    path: "riverflow2d/",
  },
  {
    key: "oilflow2d",
    match: "/oilflow2d/",
    name: "OilFlow2D",
    eyebrow: "Oil Spill Modeling",
    banner: "assets/product-brand/OF2D_top_banner.jpg",
    icon: "assets/product-brand/of2d_large_icon.png",
    logo: "assets/product-brand/of2d_logo.png",
    path: "oilflow2d/",
  },
  {
    key: "hydrobid-flood",
    match: "/hydrobid-flood/",
    name: "HydroBID Flood",
    eyebrow: "Regional Flood Modeling",
    banner: "assets/product-brand/RF2D_top_banner.jpg",
    icon: "assets/product-brand/hbf_large_icon.png",
    logo: "assets/product-brand/hbf_logo.png",
    path: "hydrobid-flood/",
  },
];

const siteWordmark = "assets/product-brand/hydronia_documentation_wordmark.png";

function currentProductBrand() {
  const path = window.location.pathname.toLowerCase();
  return productBrands.find((brand) => path.includes(brand.match));
}

function assetUrl(path) {
  const base = window.__md_scope || new URL("../", window.location.href);
  return new URL(path, base).toString();
}

function docsUrl(path) {
  const base = window.__md_scope || new URL("../", window.location.href);
  return new URL(path, base).toString();
}

function removeLegacyProductHero() {
  document.querySelector(".hy-product-hero")?.remove();
  document.querySelectorAll(".hy-product-heading").forEach((node) => {
    node.classList.remove("hy-product-heading");
  });
}

function createProductHeaderBrand(brand) {
  const link = document.createElement("a");
  link.className = "hy-product-header";
  link.href = docsUrl(brand.path);
  link.setAttribute("aria-label", `${brand.name} documentation`);

  const mark = document.createElement("span");
  mark.className = "hy-product-header__mark";

  const icon = document.createElement("img");
  icon.className = "hy-product-header__icon";
  icon.src = assetUrl(brand.icon);
  icon.alt = "";
  icon.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.className = "hy-product-header__label";
  label.textContent = brand.name;

  mark.append(icon);
  link.append(mark, label);
  return link;
}

function productNavSelector(brand) {
  return [
    `.md-tabs__link[href$="${brand.path}"]`,
    `.md-nav--primary .md-nav__link[href$="${brand.path}"]`,
  ].join(", ");
}

function installProductNavIcons() {
  document.querySelectorAll(".hy-nav-product-icon").forEach((node) => node.remove());

  productBrands.forEach((brand) => {
    document.querySelectorAll(productNavSelector(brand)).forEach((link) => {
      const icon = document.createElement("img");
      icon.className = "hy-nav-product-icon";
      icon.src = assetUrl(brand.icon);
      icon.alt = "";
      icon.setAttribute("aria-hidden", "true");
      link.prepend(icon);
    });
  });
}

function replaceHeaderTopicWithWordmark(topic) {
  if (!topic || topic.querySelector(".hy-site-wordmark")) {
    return;
  }

  topic.textContent = "";
  const img = document.createElement("img");
  img.className = "hy-site-wordmark";
  img.src = assetUrl(siteWordmark);
  img.alt = "Hydronia Documentation";
  topic.append(img);
}

function installSiteHeaderWordmark() {
  document
    .querySelectorAll(".md-header__title .md-header__topic .md-ellipsis")
    .forEach(replaceHeaderTopicWithWordmark);
}

function installProductBrandHeader() {
  const brand = currentProductBrand();
  const headerTitle = document.querySelector(".md-header__title");

  removeLegacyProductHero();
  document.querySelector(".hy-product-header")?.remove();
  installSiteHeaderWordmark();
  installProductNavIcons();

  if (!brand || !headerTitle) {
    document.body.dataset.hyProduct = "";
    document.body.style.removeProperty("--hy-product-banner");
    return;
  }

  document.body.dataset.hyProduct = brand.key;
  document.body.style.setProperty("--hy-product-banner", `url("${assetUrl(brand.banner)}")`);
  headerTitle.after(createProductHeaderBrand(brand));
}

if (typeof document$ !== "undefined") {
  document$.subscribe(installProductBrandHeader);
} else {
  document.addEventListener("DOMContentLoaded", installProductBrandHeader);
}
