'use client';

/**
 * Role icons, tabler (ux_baseline §1: "role icon overlay (tabler) where the viewer is
 * entitled to see the role"). Hand-authored pixel glyphs are reserved for the four DEATH
 * marks — a role badge is chrome, not story, so it borrows the icon set rather than the
 * art set.
 *
 * Rendered only where a role is passed in, which only happens where the fold actually
 * received one. No entitlement decision is made here.
 */
import {
  IconBlade,
  IconHeartPlus,
  IconPaw,
  IconSearch,
  IconTargetArrow,
  IconUser,
  type IconProps,
} from '@tabler/icons-react';

type IconComponent = (props: IconProps) => React.ReactNode;

const ROLE_ICONS: Record<string, IconComponent> = {
  wolf: IconPaw,
  villager: IconUser,
  healer: IconHeartPlus,
  investigator: IconSearch,
  vigilante: IconTargetArrow,
  serial_killer: IconBlade,
};

export function RoleIcon({ role, size = 13 }: { role: string; size?: number }) {
  const Icon = ROLE_ICONS[role];
  // An unknown role renders no icon rather than a placeholder: the role set is closed
  // server-side, so a miss means the wire changed and a wrong icon would hide that.
  if (!Icon) return null;
  return <Icon size={size} stroke={2} aria-hidden="true" />;
}
