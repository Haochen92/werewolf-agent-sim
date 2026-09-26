import { TicketOffice } from '../../_components/ticket/TicketOffice';

export const metadata = { title: 'Open a room' };

/** The room ticket: a room others join (ticket-office mockup, review §A4). */
export default function NewRoomPage() {
  return <TicketOffice kind="room" />;
}
