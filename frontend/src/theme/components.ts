/**
 * Per-component slice: the landing mockup's controls expressed as Mantine defaults, with the
 * look in the colocated CSS modules under `theme/components/`. Only the components the page
 * mockups use are themed; anything else renders as stock Mantine over the warm `dark` scale.
 */
import {
  Button,
  Input,
  Modal,
  Notification,
  Select,
  Switch,
  Table,
  Tabs,
  TextInput,
  Title,
  createTheme,
} from '@mantine/core';
import buttonClasses from './components/Button.module.css';
import inputClasses from './components/Input.module.css';
import overlayClasses from './components/Overlay.module.css';
import switchClasses from './components/Switch.module.css';
import tableClasses from './components/Table.module.css';
import tabsClasses from './components/Tabs.module.css';
import titleClasses from './components/Title.module.css';

export const componentsTheme = createTheme({
  components: {
    // `ghost` is the quiet default; `primary` and `brass` are the other two (Button.module.css)
    Button: Button.extend({
      defaultProps: { variant: 'ghost', size: 'md' },
      classNames: buttonClasses,
    }),
    Input: Input.extend({ defaultProps: { radius: 'xs' }, classNames: inputClasses }),
    TextInput: TextInput.extend({
      defaultProps: { radius: 'xs' },
      classNames: inputClasses,
    }),
    Select: Select.extend({ defaultProps: { radius: 'xs' }, classNames: inputClasses }),
    Switch: Switch.extend({ defaultProps: { radius: 'xl' }, classNames: switchClasses }),
    Tabs: Tabs.extend({ defaultProps: { variant: 'pills' }, classNames: tabsClasses }),
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
  },
});
