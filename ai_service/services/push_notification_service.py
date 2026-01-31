"""Push Notification Service.

Provides browser push notifications for:
- Quarterly estimated tax reminders
- Filing deadline reminders
- Document availability notifications
- Return status updates
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import os


class NotificationType(Enum):
    """Types of notifications."""
    ESTIMATED_TAX_REMINDER = "estimated_tax"
    FILING_DEADLINE = "filing_deadline"
    DOCUMENT_AVAILABLE = "document_available"
    RETURN_STATUS = "return_status"
    REFUND_STATUS = "refund_status"
    ACTION_REQUIRED = "action_required"
    TAX_TIP = "tax_tip"
    SYSTEM = "system"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class PushSubscription:
    """Web Push subscription info."""
    endpoint: str
    keys: Dict[str, str]  # p256dh and auth keys
    user_id: str
    created_at: datetime
    last_used: Optional[datetime] = None
    device_info: Optional[str] = None


@dataclass
class ScheduledNotification:
    """A scheduled notification."""
    id: str
    notification_type: NotificationType
    title: str
    body: str
    scheduled_time: datetime
    user_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    sent: bool = False
    sent_at: Optional[datetime] = None


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    user_id: str
    enabled: bool = True
    estimated_tax_reminders: bool = True
    filing_deadline_reminders: bool = True
    document_notifications: bool = True
    refund_status: bool = True
    tax_tips: bool = True
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None
    advance_days: int = 7  # Days before deadline to remind


# 2025/2026 Tax Calendar
TAX_CALENDAR_2025_2026 = {
    # 2025 Estimated Tax Due Dates (for 2025 tax year)
    "q1_estimated_2025": datetime(2025, 4, 15),
    "q2_estimated_2025": datetime(2025, 6, 16),  # 15th is Sunday
    "q3_estimated_2025": datetime(2025, 9, 15),
    "q4_estimated_2025": datetime(2026, 1, 15),

    # 2025 Filing Deadlines
    "filing_deadline_2024": datetime(2025, 4, 15),
    "extension_deadline_2024": datetime(2025, 10, 15),

    # 2026 Filing Deadlines (for 2025 tax year)
    "filing_deadline_2025": datetime(2026, 4, 15),
    "extension_deadline_2025": datetime(2026, 10, 15),

    # Important dates for tax documents
    "w2_due": datetime(2026, 1, 31),  # Employers must send W-2s by Jan 31
    "1099_due": datetime(2026, 1, 31),  # 1099s due by Jan 31

    # IRA contribution deadline (same as filing deadline)
    "ira_contribution_2025": datetime(2026, 4, 15),
}


class PushNotificationService:
    """Service for managing push notifications."""

    def __init__(self, vapid_private_key: Optional[str] = None):
        """Initialize the notification service.

        Args:
            vapid_private_key: VAPID private key for web push.
        """
        self.vapid_private_key = vapid_private_key or os.getenv("VAPID_PRIVATE_KEY")
        self.subscriptions: Dict[str, List[PushSubscription]] = {}
        self.scheduled: Dict[str, ScheduledNotification] = {}
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.notification_history: List[Dict] = []

    def register_subscription(
        self,
        user_id: str,
        endpoint: str,
        p256dh: str,
        auth: str,
        device_info: Optional[str] = None
    ) -> PushSubscription:
        """Register a new push subscription.

        Args:
            user_id: User identifier.
            endpoint: Push service endpoint URL.
            p256dh: Public key for encryption.
            auth: Auth secret.
            device_info: Optional device description.

        Returns:
            Created PushSubscription.
        """
        subscription = PushSubscription(
            endpoint=endpoint,
            keys={"p256dh": p256dh, "auth": auth},
            user_id=user_id,
            created_at=datetime.now(),
            device_info=device_info
        )

        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = []

        # Check for duplicate endpoint
        existing = next(
            (s for s in self.subscriptions[user_id] if s.endpoint == endpoint),
            None
        )
        if existing:
            # Update existing subscription
            existing.keys = subscription.keys
            existing.device_info = device_info
            return existing

        self.subscriptions[user_id].append(subscription)

        # Schedule default notifications for new user
        self._schedule_default_reminders(user_id)

        return subscription

    def unregister_subscription(self, user_id: str, endpoint: str) -> bool:
        """Unregister a push subscription.

        Args:
            user_id: User identifier.
            endpoint: Push service endpoint URL.

        Returns:
            True if subscription was found and removed.
        """
        if user_id not in self.subscriptions:
            return False

        initial_count = len(self.subscriptions[user_id])
        self.subscriptions[user_id] = [
            s for s in self.subscriptions[user_id]
            if s.endpoint != endpoint
        ]

        return len(self.subscriptions[user_id]) < initial_count

    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> NotificationPreferences:
        """Update user notification preferences.

        Args:
            user_id: User identifier.
            preferences: Preference updates.

        Returns:
            Updated NotificationPreferences.
        """
        if user_id not in self.preferences:
            self.preferences[user_id] = NotificationPreferences(user_id=user_id)

        prefs = self.preferences[user_id]

        for key, value in preferences.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        # Reschedule notifications based on new preferences
        self._reschedule_user_notifications(user_id)

        return prefs

    def get_preferences(self, user_id: str) -> NotificationPreferences:
        """Get user notification preferences."""
        if user_id not in self.preferences:
            self.preferences[user_id] = NotificationPreferences(user_id=user_id)
        return self.preferences[user_id]

    def schedule_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        scheduled_time: datetime,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> ScheduledNotification:
        """Schedule a notification for future delivery.

        Args:
            user_id: User identifier.
            notification_type: Type of notification.
            title: Notification title.
            body: Notification body text.
            scheduled_time: When to send the notification.
            data: Additional data to include.
            priority: Notification priority.

        Returns:
            Created ScheduledNotification.
        """
        # Generate unique ID
        id_source = f"{user_id}-{notification_type.value}-{scheduled_time.isoformat()}"
        notification_id = hashlib.md5(id_source.encode()).hexdigest()[:12]

        notification = ScheduledNotification(
            id=notification_id,
            notification_type=notification_type,
            title=title,
            body=body,
            scheduled_time=scheduled_time,
            user_id=user_id,
            data=data or {},
            priority=priority
        )

        self.scheduled[notification_id] = notification

        return notification

    def cancel_notification(self, notification_id: str) -> bool:
        """Cancel a scheduled notification.

        Args:
            notification_id: ID of notification to cancel.

        Returns:
            True if notification was found and cancelled.
        """
        if notification_id in self.scheduled:
            del self.scheduled[notification_id]
            return True
        return False

    def get_pending_notifications(
        self,
        user_id: Optional[str] = None,
        before: Optional[datetime] = None
    ) -> List[ScheduledNotification]:
        """Get pending notifications.

        Args:
            user_id: Filter by user (optional).
            before: Get notifications scheduled before this time (optional).

        Returns:
            List of pending ScheduledNotification objects.
        """
        notifications = [
            n for n in self.scheduled.values()
            if not n.sent
        ]

        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]

        if before:
            notifications = [n for n in notifications if n.scheduled_time <= before]

        return sorted(notifications, key=lambda n: n.scheduled_time)

    async def send_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> Dict[str, Any]:
        """Send an immediate notification to a user.

        Args:
            user_id: User identifier.
            title: Notification title.
            body: Notification body text.
            notification_type: Type of notification.
            data: Additional data to include.
            priority: Notification priority.

        Returns:
            Result with success count and any errors.
        """
        prefs = self.get_preferences(user_id)

        # Check if user has notifications enabled
        if not prefs.enabled:
            return {"success": 0, "skipped": 1, "reason": "notifications_disabled"}

        # Check notification type preference
        type_pref_map = {
            NotificationType.ESTIMATED_TAX_REMINDER: prefs.estimated_tax_reminders,
            NotificationType.FILING_DEADLINE: prefs.filing_deadline_reminders,
            NotificationType.DOCUMENT_AVAILABLE: prefs.document_notifications,
            NotificationType.REFUND_STATUS: prefs.refund_status,
            NotificationType.TAX_TIP: prefs.tax_tips,
        }

        if notification_type in type_pref_map:
            if not type_pref_map[notification_type]:
                return {"success": 0, "skipped": 1, "reason": "type_disabled"}

        # Check quiet hours
        if self._is_quiet_hours(prefs):
            return {"success": 0, "skipped": 1, "reason": "quiet_hours"}

        # Get user's subscriptions
        subscriptions = self.subscriptions.get(user_id, [])
        if not subscriptions:
            return {"success": 0, "errors": ["no_subscriptions"]}

        # Build notification payload
        payload = {
            "title": title,
            "body": body,
            "icon": "/icons/tax-icon-192.png",
            "badge": "/icons/tax-badge-72.png",
            "tag": notification_type.value,
            "data": {
                "type": notification_type.value,
                "timestamp": datetime.now().isoformat(),
                **(data or {})
            }
        }

        if priority == NotificationPriority.URGENT:
            payload["requireInteraction"] = True
            payload["vibrate"] = [200, 100, 200]

        # Send to all user subscriptions
        success_count = 0
        errors = []

        for subscription in subscriptions:
            try:
                # In production, use pywebpush or similar
                # await self._send_web_push(subscription, payload)
                success_count += 1
                subscription.last_used = datetime.now()
            except Exception as e:
                errors.append(str(e))

        # Record in history
        self.notification_history.append({
            "user_id": user_id,
            "notification_type": notification_type.value,
            "title": title,
            "sent_at": datetime.now().isoformat(),
            "success_count": success_count,
            "errors": errors
        })

        return {
            "success": success_count,
            "errors": errors
        }

    async def process_scheduled_notifications(self) -> Dict[str, Any]:
        """Process and send all due scheduled notifications.

        Returns:
            Summary of processed notifications.
        """
        now = datetime.now()
        due_notifications = self.get_pending_notifications(before=now)

        results = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }

        for notification in due_notifications:
            results["processed"] += 1

            result = await self.send_notification(
                user_id=notification.user_id,
                title=notification.title,
                body=notification.body,
                notification_type=notification.notification_type,
                data=notification.data,
                priority=notification.priority
            )

            if result.get("success", 0) > 0:
                notification.sent = True
                notification.sent_at = now
                results["sent"] += 1
            elif result.get("skipped"):
                results["skipped"] += 1
            else:
                results["failed"] += 1

        return results

    def get_tax_calendar_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get tax calendar events within a date range.

        Args:
            start_date: Start of range (default: now).
            end_date: End of range (default: 6 months from now).

        Returns:
            List of calendar events.
        """
        start = start_date or datetime.now()
        end = end_date or (start + timedelta(days=180))

        events = []

        for name, date in TAX_CALENDAR_2025_2026.items():
            if start <= date <= end:
                event_type = self._get_event_type(name)
                events.append({
                    "name": name,
                    "date": date.isoformat(),
                    "type": event_type,
                    "title": self._get_event_title(name),
                    "description": self._get_event_description(name),
                    "days_until": (date - datetime.now()).days
                })

        return sorted(events, key=lambda e: e["date"])

    def get_upcoming_reminders(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming reminder notifications for a user.

        Args:
            user_id: User identifier.
            days: Number of days to look ahead.

        Returns:
            List of upcoming reminders.
        """
        cutoff = datetime.now() + timedelta(days=days)
        pending = self.get_pending_notifications(user_id=user_id, before=cutoff)

        return [
            {
                "id": n.id,
                "type": n.notification_type.value,
                "title": n.title,
                "body": n.body,
                "scheduled_time": n.scheduled_time.isoformat(),
                "days_until": (n.scheduled_time - datetime.now()).days
            }
            for n in pending
        ]

    # Private helper methods

    def _schedule_default_reminders(self, user_id: str):
        """Schedule default tax reminders for a new user."""
        prefs = self.get_preferences(user_id)
        advance_days = prefs.advance_days

        # Estimated tax reminders
        if prefs.estimated_tax_reminders:
            for key, date in TAX_CALENDAR_2025_2026.items():
                if "estimated" in key and date > datetime.now():
                    quarter = key.replace("_estimated_2025", "").upper()
                    reminder_date = date - timedelta(days=advance_days)

                    if reminder_date > datetime.now():
                        self.schedule_notification(
                            user_id=user_id,
                            notification_type=NotificationType.ESTIMATED_TAX_REMINDER,
                            title=f"{quarter} Estimated Tax Due Soon",
                            body=f"Your {quarter} 2025 estimated tax payment is due on {date.strftime('%B %d, %Y')}.",
                            scheduled_time=reminder_date,
                            data={"deadline": date.isoformat(), "quarter": quarter},
                            priority=NotificationPriority.HIGH
                        )

        # Filing deadline reminders
        if prefs.filing_deadline_reminders:
            for key, date in TAX_CALENDAR_2025_2026.items():
                if "filing_deadline" in key and date > datetime.now():
                    year = key.replace("filing_deadline_", "")
                    reminder_date = date - timedelta(days=advance_days)

                    if reminder_date > datetime.now():
                        self.schedule_notification(
                            user_id=user_id,
                            notification_type=NotificationType.FILING_DEADLINE,
                            title=f"Tax Filing Deadline Approaching",
                            body=f"Your {year} federal tax return is due on {date.strftime('%B %d, %Y')}.",
                            scheduled_time=reminder_date,
                            data={"deadline": date.isoformat(), "tax_year": year},
                            priority=NotificationPriority.URGENT
                        )

        # Document availability reminders (W-2s, 1099s)
        if prefs.document_notifications:
            w2_date = TAX_CALENDAR_2025_2026.get("w2_due")
            if w2_date and w2_date > datetime.now():
                self.schedule_notification(
                    user_id=user_id,
                    notification_type=NotificationType.DOCUMENT_AVAILABLE,
                    title="Tax Documents Should Be Available",
                    body="W-2s and 1099s should be arriving. Check your mail and online accounts!",
                    scheduled_time=w2_date + timedelta(days=1),
                    data={"document_types": ["W-2", "1099-INT", "1099-DIV", "1099-NEC"]},
                    priority=NotificationPriority.NORMAL
                )

    def _reschedule_user_notifications(self, user_id: str):
        """Reschedule notifications based on updated preferences."""
        # Remove existing scheduled notifications for this user
        to_remove = [
            id for id, n in self.scheduled.items()
            if n.user_id == user_id and not n.sent
        ]
        for id in to_remove:
            del self.scheduled[id]

        # Reschedule based on new preferences
        self._schedule_default_reminders(user_id)

    def _is_quiet_hours(self, prefs: NotificationPreferences) -> bool:
        """Check if current time is within quiet hours."""
        if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
            return False

        current_hour = datetime.now().hour
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        if start <= end:
            return start <= current_hour < end
        else:
            # Quiet hours span midnight
            return current_hour >= start or current_hour < end

    def _get_event_type(self, event_name: str) -> str:
        """Get event type from event name."""
        if "estimated" in event_name:
            return "estimated_tax"
        elif "filing_deadline" in event_name:
            return "filing_deadline"
        elif "extension" in event_name:
            return "extension_deadline"
        elif "w2" in event_name or "1099" in event_name:
            return "document_deadline"
        elif "ira" in event_name:
            return "contribution_deadline"
        return "other"

    def _get_event_title(self, event_name: str) -> str:
        """Get human-readable title for calendar event."""
        titles = {
            "q1_estimated_2025": "Q1 2025 Estimated Tax Due",
            "q2_estimated_2025": "Q2 2025 Estimated Tax Due",
            "q3_estimated_2025": "Q3 2025 Estimated Tax Due",
            "q4_estimated_2025": "Q4 2025 Estimated Tax Due",
            "filing_deadline_2024": "2024 Tax Return Due",
            "filing_deadline_2025": "2025 Tax Return Due",
            "extension_deadline_2024": "2024 Extension Deadline",
            "extension_deadline_2025": "2025 Extension Deadline",
            "w2_due": "W-2 Forms Due from Employers",
            "1099_due": "1099 Forms Due from Payers",
            "ira_contribution_2025": "2025 IRA Contribution Deadline",
        }
        return titles.get(event_name, event_name.replace("_", " ").title())

    def _get_event_description(self, event_name: str) -> str:
        """Get description for calendar event."""
        descriptions = {
            "q1_estimated_2025": "First quarter estimated tax payment for 2025 tax year.",
            "q2_estimated_2025": "Second quarter estimated tax payment for 2025 tax year.",
            "q3_estimated_2025": "Third quarter estimated tax payment for 2025 tax year.",
            "q4_estimated_2025": "Fourth quarter estimated tax payment for 2025 tax year.",
            "filing_deadline_2024": "Deadline to file your 2024 federal tax return or request an extension.",
            "filing_deadline_2025": "Deadline to file your 2025 federal tax return or request an extension.",
            "extension_deadline_2024": "Final deadline for 2024 returns if extension was filed.",
            "extension_deadline_2025": "Final deadline for 2025 returns if extension was filed.",
            "w2_due": "Employers must provide W-2 forms to employees by this date.",
            "1099_due": "Financial institutions must provide 1099 forms by this date.",
            "ira_contribution_2025": "Last day to make IRA contributions for tax year 2025.",
        }
        return descriptions.get(event_name, "")
