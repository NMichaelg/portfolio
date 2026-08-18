const ROLE_COLOR_CLASSES = [
  "bg-role-1/15 text-role-1 border-role-1/30",
  "bg-role-2/15 text-role-2 border-role-2/30",
  "bg-role-3/15 text-role-3 border-role-3/30",
  "bg-role-4/15 text-role-4 border-role-4/30",
  "bg-role-5/15 text-role-5 border-role-5/30",
  "bg-role-6/15 text-role-6 border-role-6/30",
];

const roleColorAssignments = new Map<string, string>();
let nextColorIndex = 0;

export function getRoleColorClass(role: string): string {
  if (!roleColorAssignments.has(role)) {
    roleColorAssignments.set(
      role,
      ROLE_COLOR_CLASSES[nextColorIndex % ROLE_COLOR_CLASSES.length]
    );
    nextColorIndex++;
  }
  return roleColorAssignments.get(role)!;
}