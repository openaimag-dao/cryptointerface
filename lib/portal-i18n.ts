/**
 * Portal UI chrome translations (EN/RU/KK) — static labels only, not
 * article content. Article title/summary translation is real Claude
 * output from the backend (see backend/app/intelligence/llm/
 * news_translation.py); this file is a hand-written dictionary for the
 * fixed set of nav/button/label strings around it, since a full i18n
 * framework is more than a handful of static strings need.
 */

export const PORTAL_LANGUAGES = [
  { code: "en", label: "EN", name: "English" },
  { code: "ru", label: "RU", name: "Русский" },
  { code: "kk", label: "KK", name: "Қазақша" },
] as const;

export type PortalLanguage = (typeof PORTAL_LANGUAGES)[number]["code"];

export const PORTAL_LANGUAGE_COOKIE = "portal_lang";
export const DEFAULT_PORTAL_LANGUAGE: PortalLanguage = "en";

export function resolvePortalLanguage(value: string | undefined): PortalLanguage {
  return PORTAL_LANGUAGES.some((l) => l.code === value) ? (value as PortalLanguage) : DEFAULT_PORTAL_LANGUAGE;
}

interface PortalStrings {
  tagline: string;
  navTrending: string;
  navSearch: string;
  navTerminal: string;
  navAccount: string;
  navSignIn: string;
  homeTrendingNow: string;
  homeSeeAll: string;
  homeNoArticles: string;
  categoryNoArticles: (label: string) => string;
  trendingTitle: string;
  trendingDescription: string;
  trendingAll: string;
  trendingEmpty: string;
  searchTitle: string;
  searchPlaceholder: string;
  searchButton: string;
  searchDefaultDescription: string;
  searchMatched: (n: number) => string;
  searchNoResults: (q: string) => string;
  articleBack: string;
  articleReadFullAt: (source: string) => string;
  articleAiSummary: string;
  articleAiSummaryDisclaimer: string;
  digestLabel: string;
  digestFrom: (n: number) => string;
  marketMovers: string;
  topGainers: string;
  topLosers: string;
  marketSnapshot: string;
  shareLabel: string;
  shareCopyLink: string;
  shareCopied: string;
  rssFeed: string;
  footerTagline: string;
}

const STRINGS: Record<PortalLanguage, PortalStrings> = {
  en: {
    tagline: "Crypto · AI · Blockchain · Innovation",
    navTrending: "Trending",
    navSearch: "Search",
    navTerminal: "Terminal ↗",
    navAccount: "Account",
    navSignIn: "Sign in",
    homeTrendingNow: "Trending Now",
    homeSeeAll: "See all",
    homeNoArticles: "No articles yet. Check back soon.",
    categoryNoArticles: (label) => `No ${label} articles yet. Check back soon.`,
    trendingTitle: "Trending",
    trendingDescription:
      "Ranked by real coverage: how many independent sources reported it and how significant the classifier scored it — not a fabricated view counter.",
    trendingAll: "All",
    trendingEmpty: "Nothing trending in the last 48 hours yet. Check back soon.",
    searchTitle: "Search",
    searchPlaceholder: "Search articles…",
    searchButton: "Search",
    searchDefaultDescription: "Search across all AIMAG News articles",
    searchMatched: (n) => `${n} article${n === 1 ? "" : "s"} matched`,
    searchNoResults: (q) => `No articles matched “${q}”.`,
    articleBack: "← Back to AIMAG News",
    articleReadFullAt: (source) => `Read the full article at ${source}`,
    articleAiSummary: "AI Summary",
    articleAiSummaryDisclaimer:
      "Generated from this article by AIMAG's AI — always verify against the original reporting below.",
    digestLabel: "AI Digest",
    digestFrom: (n) => `From ${n} article${n === 1 ? "" : "s"}`,
    marketMovers: "Market Movers",
    topGainers: "Top Gainers",
    topLosers: "Top Losers",
    marketSnapshot: "Markets",
    shareLabel: "Share",
    shareCopyLink: "Copy link",
    shareCopied: "Copied!",
    rssFeed: "RSS Feed",
    footerTagline:
      "Crypto, AI, Blockchain & Innovation headlines — aggregated from real sources and classified automatically. Every story links back to its original publisher.",
  },
  ru: {
    tagline: "Крипто · ИИ · Блокчейн · Инновации",
    navTrending: "В тренде",
    navSearch: "Поиск",
    navTerminal: "Терминал ↗",
    navAccount: "Аккаунт",
    navSignIn: "Войти",
    homeTrendingNow: "Сейчас в тренде",
    homeSeeAll: "Все новости",
    homeNoArticles: "Пока нет статей. Загляните позже.",
    categoryNoArticles: (label) => `Пока нет статей в разделе «${label}». Загляните позже.`,
    trendingTitle: "В тренде",
    trendingDescription:
      "Рейтинг по реальному охвату: сколько независимых источников написали об этом и насколько значимым это оценил классификатор — без искусственных счётчиков просмотров.",
    trendingAll: "Все",
    trendingEmpty: "Пока нет трендовых новостей за последние 48 часов. Загляните позже.",
    searchTitle: "Поиск",
    searchPlaceholder: "Поиск статей…",
    searchButton: "Найти",
    searchDefaultDescription: "Поиск по всем статьям AIMAG News",
    searchMatched: (n) => `Найдено статей: ${n}`,
    searchNoResults: (q) => `По запросу «${q}» ничего не найдено.`,
    articleBack: "← Назад к AIMAG News",
    articleReadFullAt: (source) => `Читать статью полностью на ${source}`,
    articleAiSummary: "ИИ-резюме",
    articleAiSummaryDisclaimer:
      "Сгенерировано ИИ AIMAG на основе этой статьи — всегда сверяйтесь с оригинальным источником ниже.",
    digestLabel: "ИИ-дайджест",
    // Sidesteps Russian numeral-noun agreement (1 статья / 2 статьи / 5
    // статей) the same way timeAgo() does — a fixed invariant label
    // reads naturally in Russian regardless of the count.
    digestFrom: (n) => `Источников: ${n}`,
    marketMovers: "Движения рынка",
    topGainers: "Растут больше всех",
    topLosers: "Падают больше всех",
    marketSnapshot: "Мировые рынки",
    shareLabel: "Поделиться",
    shareCopyLink: "Скопировать ссылку",
    shareCopied: "Скопировано!",
    rssFeed: "RSS-лента",
    footerTagline:
      "Новости о крипте, ИИ, блокчейне и инновациях — собраны из реальных источников и классифицированы автоматически. Каждая новость ведёт к оригинальному источнику.",
  },
  kk: {
    tagline: "Крипто · ЖИ · Блокчейн · Инновация",
    navTrending: "Трендте",
    navSearch: "Іздеу",
    navTerminal: "Терминал ↗",
    navAccount: "Аккаунт",
    navSignIn: "Кіру",
    homeTrendingNow: "Қазір трендте",
    homeSeeAll: "Барлығын көру",
    homeNoArticles: "Әзірге мақалалар жоқ. Кейінірек қараңыз.",
    categoryNoArticles: (label) => `«${label}» бөлімінде әзірге мақалалар жоқ. Кейінірек қараңыз.`,
    trendingTitle: "Трендте",
    trendingDescription:
      "Нақты қамту бойынша реттелген: оқиға туралы қанша тәуелсіз дереккөз жазғаны және классификатор оны қаншалықты маңызды деп бағалағаны — жасанды қаралым саны емес.",
    trendingAll: "Барлығы",
    trendingEmpty: "Соңғы 48 сағатта трендте ештеңе жоқ. Кейінірек қараңыз.",
    searchTitle: "Іздеу",
    searchPlaceholder: "Мақалаларды іздеу…",
    searchButton: "Іздеу",
    searchDefaultDescription: "AIMAG News барлық мақалалары бойынша іздеу",
    searchMatched: (n) => `Табылған мақалалар: ${n}`,
    searchNoResults: (q) => `«${q}» бойынша ештеңе табылмады.`,
    articleBack: "← AIMAG News-ке оралу",
    articleReadFullAt: (source) => `Толық мақаланы ${source} сайтынан оқыңыз`,
    articleAiSummary: "ЖИ түйіндемесі",
    articleAiSummaryDisclaimer:
      "Бұл мақала негізінде AIMAG ЖИ жасаған — әрқашан төмендегі түпнұсқа дереккөзбен салыстырыңыз.",
    digestLabel: "ЖИ дайджесті",
    digestFrom: (n) => `Дереккөздер: ${n}`,
    marketMovers: "Нарық қозғалысы",
    topGainers: "Ең көп өскендер",
    topLosers: "Ең көп түскендер",
    marketSnapshot: "Әлемдік нарықтар",
    shareLabel: "Бөлісу",
    shareCopyLink: "Сілтемені көшіру",
    shareCopied: "Көшірілді!",
    rssFeed: "RSS-таспа",
    footerTagline:
      "Крипто, ЖИ, блокчейн және инновациялар туралы жаңалықтар — нақты дереккөздерден жиналып, автоматты түрде жіктелген. Әр жаңалық түпнұсқа дереккөзге сілтеме береді.",
  },
};

export function portalStrings(lang: PortalLanguage): PortalStrings {
  return STRINGS[lang];
}

interface TopicI18n {
  label: string;
  description: string;
}

const TOPIC_STRINGS: Record<PortalLanguage, Record<string, TopicI18n>> = {
  en: {
    CRYPTO: { label: "Crypto", description: "Markets, exchanges, and on-chain activity" },
    AI: { label: "AI", description: "Artificial intelligence research, products, and policy" },
    BLOCKCHAIN: { label: "Blockchain", description: "Protocols, infrastructure, and Web3 development" },
    INNOVATION: { label: "Innovation", description: "Emerging tech across the industry" },
  },
  ru: {
    CRYPTO: { label: "Крипто", description: "Рынки, биржи и активность в блокчейне" },
    AI: { label: "ИИ", description: "Исследования, продукты и политика в сфере искусственного интеллекта" },
    BLOCKCHAIN: { label: "Блокчейн", description: "Протоколы, инфраструктура и разработка Web3" },
    INNOVATION: { label: "Инновации", description: "Новые технологии по всей индустрии" },
  },
  kk: {
    CRYPTO: { label: "Крипто", description: "Нарықтар, биржалар және блокчейндегі белсенділік" },
    AI: { label: "ЖИ", description: "Жасанды интеллект саласындағы зерттеулер, өнімдер және саясат" },
    BLOCKCHAIN: { label: "Блокчейн", description: "Хаттамалар, инфрақұрылым және Web3 әзірлемелері" },
    INNOVATION: { label: "Инновация", description: "Салада пайда болып жатқан жаңа технологиялар" },
  },
};

export function topicStrings(lang: PortalLanguage, topicValue: string): TopicI18n {
  return TOPIC_STRINGS[lang][topicValue] ?? TOPIC_STRINGS.en[topicValue];
}

// Display labels for the Market Snapshot widget's fixed set of indices/
// commodities (backend/app/intelligence/macro/symbols.py's `id`s) —
// deliberately short ("S&P 500", not the backend's "S&P 500 (SPY proxy)",
// which is aimed at the trading terminal's more technical audience).
const MACRO_LABELS: Record<PortalLanguage, Record<string, string>> = {
  en: {
    dow: "Dow Jones",
    sp500: "S&P 500",
    nasdaq: "Nasdaq",
    gold: "Gold",
    silver: "Silver",
    oil: "Crude Oil (WTI)",
    brent: "Crude Oil (Brent)",
  },
  ru: {
    dow: "Dow Jones",
    sp500: "S&P 500",
    nasdaq: "Nasdaq",
    gold: "Золото",
    silver: "Серебро",
    oil: "Нефть (WTI)",
    brent: "Нефть (Brent)",
  },
  kk: {
    dow: "Dow Jones",
    sp500: "S&P 500",
    nasdaq: "Nasdaq",
    gold: "Алтын",
    silver: "Күміс",
    oil: "Мұнай (WTI)",
    brent: "Мұнай (Brent)",
  },
};

export function macroLabel(lang: PortalLanguage, indicatorId: string): string {
  return MACRO_LABELS[lang][indicatorId] ?? indicatorId;
}
