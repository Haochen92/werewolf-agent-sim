'use client';

import { useState, type ReactNode } from 'react';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiError } from '@/lib/request';
import { theme } from '@/theme';

export function Providers({ children }: { children: ReactNode }) {
  // Created in a useState initialiser, not at module scope: the App Router renders this on
  // the server too, and a module-level client would be shared across requests.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: (failureCount, error) => {
              // A 4xx is the server's considered answer, not a blip — retrying it just
              // delays the error state the UI already knows how to render.
              if (error instanceof ApiError && error.status < 500) return false;
              return failureCount < 2;
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {/* forced, not default: there is no light theme to switch to (see layout.tsx) */}
      <MantineProvider theme={theme} forceColorScheme="dark">
        <Notifications position="top-right" />
        {children}
      </MantineProvider>
    </QueryClientProvider>
  );
}
