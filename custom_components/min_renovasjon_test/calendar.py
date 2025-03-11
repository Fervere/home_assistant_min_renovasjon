"""Calendar platform for min_renovasjon."""
from datetime import datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import callback
from homeassistant.util.dt import as_utc

from .const import DOMAIN, CALENDAR_NAME


class MinRenovasjonCalendarEntity(CalendarEntity):
    """Representation of a Min Renovasjon Calendar Entity."""

    def __init__(self, hass, min_renovasjon, config_entry):
        """Initialize the calendar entity."""
        self._hass = hass
        self._min_renovasjon = min_renovasjon
        self._name = CALENDAR_NAME
        self._events = []
        self.config_entry = config_entry
        
    @property
    def name(self):
        """Return the name of the calendar entity."""
        return self._name

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._get_next_event()
    
    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}_calendar"

    async def async_get_events(
        self,
        hass,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        start_date = as_utc(start_date)
        end_date = as_utc(end_date)
        
        # Fetch updated calendar data
        self._events = await self._fetch_events()
        
        # Filter events to include only those within the requested date range
        return [
            event for event in self._events
            if start_date <= as_utc(event.start) <= end_date or
            start_date <= as_utc(event.end) <= end_date or
            (as_utc(event.start) <= start_date and end_date <= as_utc(event.end))
        ]
    
    async def async_update(self):
        """Update the calendar with new events from the API."""
        self._events = await self._fetch_events()

    async def _fetch_events(self):
        """Fetch calendar events from Min Renovasjon data."""
        events = []
        
        # Get the calendar list from min_renovasjon
        calendar_list = await self._min_renovasjon.get_calendar_list()
        
        if calendar_list:
            for entry in calendar_list:
                if entry is None:
                    continue
                    
                fraction_id, fraction_name, _, pickup_date, next_pickup_date = entry
                
                # Create an event for the upcoming pickup
                if pickup_date and pickup_date.date() >= datetime.now().date():
                    event_start = pickup_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    event_end = event_start + timedelta(days=1)
                    
                    events.append(
                        CalendarEvent(
                            summary=f"{fraction_name} tømming",
                            start=event_start,
                            end=event_end,
                            description=f"Tømming av {fraction_name}",
                        )
                    )
                
                # Create an event for the next pickup after that
                if next_pickup_date and next_pickup_date.date() >= datetime.now().date():
                    event_start = next_pickup_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    event_end = event_start + timedelta(days=1)
                    
                    events.append(
                        CalendarEvent(
                            summary=f"{fraction_name} tømming",
                            start=event_start,
                            end=event_end,
                            description=f"Tømming av {fraction_name}",
                        )
                    )
        
        # Sort events by start date
        events.sort(key=lambda x: x.start)
        return events

    def _get_next_event(self):
        """Return the next upcoming event."""
        now = datetime.now()
        future_events = [
            event for event in self._events
            if event.start >= now
        ]
        
        if not future_events:
            return None
            
        return min(future_events, key=lambda x: x.start)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the calendar platform."""
    min_renovasjon = hass.data[DOMAIN]["data"]
    
    async_add_entities([MinRenovasjonCalendarEntity(hass, min_renovasjon, config_entry)])
