import { TicketOffice } from '../_components/ticket/TicketOffice';

export const metadata = { title: 'Play' };

/** The solo ticket: one seat against eight agents (ticket-office mockup, review §A4). */
export default function PlayPage() {
  return <TicketOffice kind="solo" />;
}
