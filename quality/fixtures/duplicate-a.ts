/**
 * Fixture: TypeScript file with a code block duplicated in duplicate-b.ts.
 * Used by acceptance tests to verify the duplication gate catches new clones.
 * Excluded from production scanning via .jscpd.json ignore list.
 */

interface UserConfig {
  name: string;
  email: string;
  role: "admin" | "user" | "viewer";
}

function validateUserConfig(config: UserConfig): boolean {
  if (!config.name || config.name.length < 2) {
    return false;
  }
  if (!config.email || !config.email.includes("@")) {
    return false;
  }
  if (!["admin", "user", "viewer"].includes(config.role)) {
    return false;
  }
  return true;
}

function formatUserDisplay(config: UserConfig): string {
  const roleLabel = config.role.charAt(0).toUpperCase() + config.role.slice(1);
  return `${config.name} (${config.email}) [${roleLabel}]`;
}

export { validateUserConfig, formatUserDisplay };
export type { UserConfig };
