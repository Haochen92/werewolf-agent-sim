/**
 * The switch that turns role cards over to their briefings: under the landing's card, and in
 * each side's banner in the guide (where it turns that side's whole row). Mantine's Switch,
 * re-dressed as a pill on the dark site through its Styles API.
 */
import { Switch } from '@mantine/core';
import classes from './BriefingsSwitch.module.css';

/** Two cards side by side, the second dashed for its back, under a turning arrow. */
function FlipIcon() {
  return (
    <svg className={classes.icon} viewBox="0 0 24 24" aria-hidden="true">
      <rect x="2.5" y="8" width="8.5" height="12.5" rx="1.6" />
      <rect x="13" y="8" width="8.5" height="12.5" rx="1.6" strokeDasharray="2 2.2" />
      <path d="M6.5 5.5C9 2.6 15 2.6 17.5 5.5" />
      <path d="M15.2 5.9l2.5-.2-.3-2.5" />
    </svg>
  );
}

export function BriefingsSwitch({
  checked,
  onChange,
  ariaLabel,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** Names what it turns when the visible word alone would not ("Town briefings"). */
  ariaLabel?: string;
}) {
  return (
    <Switch
      checked={checked}
      onChange={(e) => onChange(e.currentTarget.checked)}
      labelPosition="left"
      label={
        <>
          <FlipIcon />
          Briefings
        </>
      }
      aria-label={ariaLabel}
      classNames={{
        root: classes.root,
        body: classes.body,
        labelWrapper: classes.labelWrapper,
        label: classes.label,
        track: classes.track,
        thumb: classes.thumb,
      }}
    />
  );
}
