import { availabilityFor } from '@/components/layout/navAvailability';

/**
 * "Coming soon" next to a dashboard tile's label when the tile links to a
 * page this version leaves out (navAvailability). The tile still opens the
 * "Coming soon" page, which links back to the dashboard.
 */
export function ComingSoonTag({ href }: { href: string }) {
  if (!availabilityFor(href)) return null;
  return (
    <span className="ml-2 align-middle text-[10px] font-normal text-slate-400">Coming soon</span>
  );
}

export default ComingSoonTag;
