export const EMAILABLE_EVENT_TYPES = [
  'New Item',
  'Restocked',
  'Price Change',
] as const

export type EmailableEventType = (typeof EMAILABLE_EVENT_TYPES)[number]

export const EVENT_TYPE_PREF_OPTIONS: {
  event_type: EmailableEventType
  label: string
  description: string
}[] = [
  {
    event_type: 'New Item',
    label: 'New items',
    description: 'A title appears in the catalog for the first time',
  },
  {
    event_type: 'Restocked',
    label: 'Restocks',
    description: 'A previously out-of-stock book is available again',
  },
  {
    event_type: 'Price Change',
    label: 'Price changes',
    description: 'Meaningful price drops or increases on in-stock books',
  },
]
