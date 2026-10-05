"""
Profile Manager - Widget for managing birth profiles.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox,
    QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from typing import List, Optional

from astro_core.controllers import ProfileController
from astro_core.controllers.profile_controller import BirthProfile


class ProfileManager(QWidget):
    """Widget for managing birth profiles."""
    
    # Signals
    profile_selected = pyqtSignal(object)  # BirthProfile
    profile_deleted = pyqtSignal(str)
    profile_edited = pyqtSignal(str)
    
    def __init__(self, profile_controller: ProfileController, parent=None):
        super().__init__(parent)
        self._profile_controller = profile_controller
        self._profiles: List[BirthProfile] = []
        
        self._init_ui()
        self.refresh()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Profile list
        self.list_profiles = QListWidget()
        self.list_profiles.setAlternatingRowColors(True)
        self.list_profiles.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_profiles)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_new = QPushButton("➕ Новый")
        self.btn_load = QPushButton("📂 Загрузить")
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_delete = QPushButton("🗑️ Удалить")
        
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)
        
        # Connect
        self.btn_new.clicked.connect(self._on_new)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        
    def refresh(self):
        """Refresh profile list."""
        self.list_profiles.clear()
        self._profiles = self._profile_controller.list_profiles()
        
        for profile in self._profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.ItemDataRole.UserRole, profile.name)
            # Add tooltip with details
            tooltip = (
                f"Дата: {profile.birth_date.strftime('%d.%m.%Y')}\n"
                f"Время: {profile.birth_time.strftime('%H:%M')}\n"
                f"Координаты: {profile.latitude:.4f}, {profile.longitude:.4f}\n"
                f"UTC: {profile.utc_offset_hours:+.1f}"
            )
            if profile.created_at:
                tooltip += f"\nСоздан: {profile.created_at}"
            item.setToolTip(tooltip)
            self.list_profiles.addItem(item)
            
    def _get_selected_profile_name(self) -> Optional[str]:
        """Get currently selected profile name."""
        item = self.list_profiles.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
        
    def _get_selected_profile(self) -> Optional[BirthProfile]:
        """Get currently selected profile object."""
        name = self._get_selected_profile_name()
        if name:
            for p in self._profiles:
                if p.name == name:
                    return p
        return None
        
    def _on_new(self):
        """Create new profile from current form (handled by parent)."""
        # This will be handled by the main window
        pass
        
    def _on_load(self):
        """Load selected profile."""
        profile = self._get_selected_profile()
        if profile:
            self.profile_selected.emit(profile)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для загрузки")
            
    def _on_edit(self):
        """Edit selected profile."""
        name = self._get_selected_profile_name()
        if name:
            self.profile_edited.emit(name)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для редактирования")
            
    def _on_delete(self):
        """Delete selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Выберите профиль для удаления")
            return
            
        reply = QMessageBox.question(
            self, "Удалить профиль",
            f"Удалить профиль '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_deleted.emit(name)
            
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Load profile on double click."""
        self._on_load()
        
    @pyqtSlot()
    def on_profile_saved(self):
        """Called when a profile is saved."""
        self.refresh()