/**
 * Fixture: TypeScript file with a code block cloned from duplicate-a.ts.
 * Used by acceptance tests to verify the duplication gate catches new clones.
 * Excluded from production scanning via .jscpd.json ignore list.
 */

interface MemberConfig {
  username: string;
  address: string;
  level: "owner" | "member" | "guest";
}

function validateMemberConfig(config: MemberConfig): boolean {
  if (!config.username || config.username.length < 2) {
    return false;
  }
  if (!config.address || !config.address.includes("@")) {
    return false;
  }
  if (!["owner", "member", "guest"].includes(config.level)) {
    return false;
  }
  return true;
}

function formatMemberDisplay(config: MemberConfig): string {
  const levelLabel = config.level.charAt(0).toUpperCase() + config.level.slice(1);
  return `${config.username} (${config.address}) [${levelLabel}]`;
}

export { validateMemberConfig, formatMemberDisplay };
export type { MemberConfig };
