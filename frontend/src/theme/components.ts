/**
 * Per-component slice: the landing mockup's controls expressed as Mantine defaults, with the
 * look in the colocated CSS modules under `theme/components/`. Only the components the page
 * mockups use are themed; anything else renders as stock Mantine over the warm `dark` scale.
 */
import {
  Alert,
  Anchor,
  Button,
  Chip,
  Input,
  Modal,
  Notification,
  SegmentedControl,
  Select,
  Switch,
  Table,
  TextInput,
  Title,
  createTheme,
} from '@mantine/core';
import alertClasses from './components/Alert.module.css';
import anchorClasses from './components/Anchor.module.css';
import buttonClasses from './components/Button.module.css';
import chipClasses from './components/Chip.module.css';
import inputClasses from './components/Input.module.css';
import overlayClasses from './components/Overlay.module.css';
import segmentedClasses from './components/SegmentedControl.module.css';
import switchClasses from './components/Switch.module.css';
import tableClasses from './components/Table.module.css';
import titleClasses from './components/Title.module.css';

export const componentsTheme = createTheme({
  components: {
    // `well` is the default; `brass` is the main action, `text` a word that acts (Button.module.css)
    Button: Button.extend({
      defaultProps: { variant: 'well', size: 'md' },
      classNames: buttonClasses,
    }),
    // the site's link: the surface's accent, always underlined (Anchor.module.css)
    Anchor: Anchor.extend({ defaultProps: { underline: 'always' }, classNames: anchorClasses }),
    Input: Input.extend({ defaultProps: { radius: 'xs' }, classNames: inputClasses }),
    TextInput: TextInput.extend({
      defaultProps: { radius: 'xs' },
      classNames: inputClasses,
    }),
    Select: Select.extend({ defaultProps: { radius: 'xs' }, classNames: inputClasses }),
    SegmentedControl: SegmentedControl.extend({
      defaultProps: { radius: 'xs' },
      classNames: segmentedClasses,
    }),
    // the filter pills carry no check mark: the lit pill is the state
    Chip: Chip.extend({
      defaultProps: { variant: 'outline', icon: null },
      classNames: chipClasses,
    }),
    Switch: Switch.extend({ defaultProps: { radius: 'xl' }, classNames: switchClasses }),
    Modal: Modal.extend({ defaultProps: { radius: 'sm' }, classNames: overlayClasses }),
    Notification: Notification.extend({
      defaultProps: { radius: 'sm', color: 'amber' },
      classNames: overlayClasses,
    }),
    Table: Table.extend({
      defaultProps: { verticalSpacing: 11, horizontalSpacing: 14 },
      classNames: tableClasses,
    }),
    Title: Title.extend({ classNames: titleClasses }),
    Alert: Alert.extend({
      defaultProps: { radius: 'xs', variant: 'light', color: 'wolf' },
      classNames: alertClasses,
    }),
  },
});
