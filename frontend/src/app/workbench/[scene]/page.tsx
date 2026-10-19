/**
 * The workbench (stage_architecture.md §7): one route that mounts any scene exactly as the
 * replay and the live game will, drawn from the bundled fixture game, with every choice in
 * the URL. `/workbench/paint` is the backdrop bench, for the paint generators on their own.
 */
import { Suspense } from 'react';
import { Workbench } from './_components/Workbench';

export default function WorkbenchScenePage() {
  return (
    <Suspense>
      <Workbench />
    </Suspense>
  );
}
