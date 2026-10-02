/**
 * Lesson_Catalog - Defines all available lessons with metadata.
 * Each lesson has: id, slug, bilingual title, track, difficulty,
 * estimatedMinutes, prerequisites.
 *
 * The catalog is organized into three tracks for the agentic-AI learning
 * session:
 *   - "morning"   : Understanding the Fundamentals
 *   - "afternoon" : Designing and Governing AI Agents
 *   - "sandbox"   : opcp-explorer platform operations the agents act upon
 *
 * Validates: Requirements 1.3
 */

/**
 * @typedef {Object} LessonTitle
 * @property {string} en - English title
 * @property {string} fr - French title
 */

/**
 * @typedef {Object} Lesson
 * @property {string} id - Unique lesson identifier
 * @property {string} slug - URL-friendly slug
 * @property {LessonTitle} title - Bilingual title object
 * @property {"morning"|"afternoon"|"sandbox"} track - Session track grouping
 * @property {"beginner"|"intermediate"|"advanced"} difficulty - Lesson difficulty level
 * @property {number} estimatedMinutes - Estimated completion time (1-480)
 * @property {string[]} prerequisites - Array of prerequisite lesson ids
 */

/** @type {Lesson[]} */
export const lessons = [
  // ---------------------------------------------------------------------------
  // Morning — Understanding the Fundamentals
  // ---------------------------------------------------------------------------
  {
    id: "assistant-vs-agent",
    slug: "assistant-vs-agent",
    title: {
      en: "From Assistant to Agent: the Autonomy Spectrum",
      fr: "De l'assistant à l'agent : le spectre d'autonomie"
    },
    track: "morning",
    difficulty: "beginner",
    estimatedMinutes: 30,
    prerequisites: []
  },
  {
    id: "agent-anatomy-7-components",
    slug: "agent-anatomy-7-components",
    title: {
      en: "Anatomy of an AI Agent: the Seven Core Components",
      fr: "Anatomie d'un agent IA : les sept composants essentiels"
    },
    track: "morning",
    difficulty: "beginner",
    estimatedMinutes: 45,
    prerequisites: ["assistant-vs-agent"]
  },
  {
    id: "agentic-loop-and-variants",
    slug: "agentic-loop-and-variants",
    title: {
      en: "The Agentic Loop: Think → Act → Observe and its Variants",
      fr: "La boucle agentique : Penser → Agir → Observer et ses variantes"
    },
    track: "morning",
    difficulty: "intermediate",
    estimatedMinutes: 45,
    prerequisites: ["agent-anatomy-7-components"]
  },
  {
    id: "stopping-criteria",
    slug: "stopping-criteria",
    title: {
      en: "Stopping Criteria: Preventing Infinite Loops",
      fr: "Critères d'arrêt : prévenir les boucles infinies"
    },
    track: "morning",
    difficulty: "intermediate",
    estimatedMinutes: 30,
    prerequisites: ["agentic-loop-and-variants"]
  },

  // ---------------------------------------------------------------------------
  // Afternoon — Designing and Governing AI Agents
  // ---------------------------------------------------------------------------
  {
    id: "multi-agent-patterns",
    slug: "multi-agent-patterns",
    title: {
      en: "Multi-Agent Systems: Four Architectural Patterns",
      fr: "Systèmes multi-agents : quatre patrons d'architecture"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 45,
    prerequisites: ["stopping-criteria"]
  },
  {
    id: "when-not-multi-agent",
    slug: "when-not-multi-agent",
    title: {
      en: "When Not to Use a Multi-Agent Architecture",
      fr: "Quand ne pas utiliser une architecture multi-agents"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 30,
    prerequisites: ["multi-agent-patterns"]
  },
  {
    id: "guardrails-5-layers",
    slug: "guardrails-5-layers",
    title: {
      en: "Guardrails: the Five Layers of Control",
      fr: "Garde-fous : les cinq couches de contrôle"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 45,
    prerequisites: ["when-not-multi-agent"]
  },
  {
    id: "human-in-the-loop-ovhcloud-policy",
    slug: "human-in-the-loop-ovhcloud-policy",
    title: {
      en: "Human-in-the-Loop Governance and the OVHcloud AI Policy",
      fr: "Gouvernance human-in-the-loop et la politique IA OVHcloud"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 30,
    prerequisites: ["guardrails-5-layers"]
  },
  {
    id: "threat-modeling-workshop",
    slug: "threat-modeling-workshop",
    title: {
      en: "Workshop: Threat Modeling an AI Agent",
      fr: "Atelier : modélisation des menaces d'un agent IA"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 45,
    prerequisites: ["human-in-the-loop-ovhcloud-policy"]
  },
  {
    id: "agent-design-capstone",
    slug: "agent-design-capstone",
    title: {
      en: "Capstone: Designing an AI Agent End to End",
      fr: "Projet final : concevoir un agent IA de bout en bout"
    },
    track: "afternoon",
    difficulty: "advanced",
    estimatedMinutes: 60,
    prerequisites: ["threat-modeling-workshop"]
  },

  // ---------------------------------------------------------------------------
  // Sandbox — opcp-explorer platform operations (the agent's environment)
  // ---------------------------------------------------------------------------
  {
    id: "install-bare-metal",
    slug: "install-bare-metal",
    title: {
      en: "Installation on Bare-Metal Ubuntu with Agentic AI",
      fr: "Installation sur Ubuntu Bare-Metal avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "beginner",
    estimatedMinutes: 120,
    prerequisites: []
  },
  {
    id: "adding-applications",
    slug: "adding-applications",
    title: {
      en: "Adding New Applications with Agentic AI",
      fr: "Ajout de nouvelles applications avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "beginner",
    estimatedMinutes: 60,
    prerequisites: ["install-bare-metal"]
  },
  {
    id: "starting-applications",
    slug: "starting-applications",
    title: {
      en: "Starting Applications with Agentic AI",
      fr: "Démarrage des applications avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "beginner",
    estimatedMinutes: 60,
    prerequisites: ["adding-applications"]
  },
  {
    id: "stopping-applications",
    slug: "stopping-applications",
    title: {
      en: "Stopping Applications with Agentic AI",
      fr: "Arrêt des applications avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "beginner",
    estimatedMinutes: 45,
    prerequisites: ["starting-applications"]
  },
  {
    id: "making-backups",
    slug: "making-backups",
    title: {
      en: "Making Backups with Agentic AI",
      fr: "Création de sauvegardes avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "intermediate",
    estimatedMinutes: 90,
    prerequisites: ["install-bare-metal"]
  },
  {
    id: "modifying-applications",
    slug: "modifying-applications",
    title: {
      en: "Modifying Existing Applications with Agentic AI",
      fr: "Modification des applications existantes avec l'IA agentique"
    },
    track: "sandbox",
    difficulty: "intermediate",
    estimatedMinutes: 90,
    prerequisites: ["adding-applications"]
  }
];

/**
 * Find a lesson by its slug.
 * @param {string} slug - The lesson slug to search for
 * @returns {Lesson|undefined} The matching lesson or undefined if not found
 */
export function getLessonBySlug(slug) {
  return lessons.find((lesson) => lesson.slug === slug);
}

/**
 * Get all lessons matching a given difficulty level.
 * @param {"beginner"|"intermediate"|"advanced"} difficulty - The difficulty to filter by
 * @returns {Lesson[]} Array of lessons with the specified difficulty
 */
export function getLessonsByDifficulty(difficulty) {
  return lessons.filter((lesson) => lesson.difficulty === difficulty);
}

/**
 * Get all lessons belonging to a given session track.
 * @param {"morning"|"afternoon"|"sandbox"} track - The track to filter by
 * @returns {Lesson[]} Array of lessons in the specified track, in catalog order
 */
export function getLessonsByTrack(track) {
  return lessons.filter((lesson) => lesson.track === track);
}

/**
 * Get the full prerequisite chain for a given lesson (recursive, depth-first).
 * Returns all lessons that must be completed before the specified lesson,
 * ordered from earliest prerequisite to the immediate prerequisite.
 * Each lesson appears at most once in the result (no duplicates).
 *
 * @param {string} lessonId - The lesson id to get prerequisites for
 * @returns {string[]} Ordered array of prerequisite lesson ids (earliest first)
 */
export function getPrerequisiteChain(lessonId) {
  const visited = new Set();
  const chain = [];

  function collect(id) {
    if (visited.has(id)) {
      return;
    }
    visited.add(id);

    const lesson = lessons.find((l) => l.id === id);
    if (!lesson) {
      return;
    }

    for (const prereqId of lesson.prerequisites) {
      collect(prereqId);
    }

    // Add the lesson after its prerequisites (topological order)
    // but don't include the originally requested lesson itself
    if (id !== lessonId) {
      chain.push(id);
    }
  }

  collect(lessonId);
  return chain;
}
