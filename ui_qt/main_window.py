"""
Main Window - PyQt6 desktop application main window.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QTabWidget, QMessageBox,
    QLabel, QProgressBar, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from typing import Optional

from astro_core.controllers import (
    ChartController,
    TransitController,
    ProgressionController,
    DisplayProfileController,
    CityController,
    ProfileController,
)
from astro_core.state import StateManager

# Import widgets
from ui_qt.widgets import (
    ChartView,
    BirthInputPanel,
    TransitPanel,
    ProgressionPanel,
    ProfileManager,
    DisplayProfileEditor,
    CitySelector
)
from ui_qt.models.chart_model import (
    create_model_for_objects,
    create_model_for_houses,
    create_model_for_aspects,
    create_model_for_transit_calendar,
    create_model_for_transit_precise,
    create_model_for_transit_periods,
    create_model_for_progression_planets,
    create_model_for_progression_aspects
)
from ui_qt.dialogs.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Astro Processor")
        self.setMinimumSize(1024, 768)
        self.resize(1400, 900)
        
        # Initialize controllers and state
        self._chart_controller = ChartController()
        self._transit_controller = TransitController()
        self._progression_controller = ProgressionController()
        self._display_profile_controller = DisplayProfileController()
        self._city_controller = CityController()
        self._profile_controller = ProfileController()
        self._state_manager = StateManager()
        
        # State tracking
        self._current_birth_data = None
        self._current_chart_result = None
        self._current_display_profile_name = "full"
        
        # Track widgets
        self._widgets_initialized = False
        
        self._init_ui()
        self._init_menus()
        self._init_toolbars()
        self._init_status_bar()
        self._connect_signals()
        self._load_state()
        
        # Initialize charts
        self._update_chart_view()
        
    def _init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - horizontal splitter with 3 panes
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter with 3 panes: Left | Center (Chart) | Right
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self._main_splitter)
        
        # LEFT PANE - Birth input and profile manager
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)
        
        # Birth input panel
        self._birth_input_panel = BirthInputPanel(
            self._city_controller,
            self._profile_controller
        )
        left_layout.addWidget(self._birth_input_panel)
        
        # Load display profiles into birth input panel
        self._birth_input_panel._load_display_profiles()
        
        # Profile manager
        self._profile_manager = ProfileManager(self._profile_controller)
        left_layout.addWidget(self._profile_manager)
        
        # CENTER PANE - Chart View (main focus)
        self._chart_view = ChartView()
        
        # RIGHT PANE - Tabbed interface for calculations
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)
        
        # Tab widget for transit/progression panels
        self._calc_tabs = QTabWidget()
        
        # Transit panel
        self._transit_panel = TransitPanel(
            self._transit_controller,
            self._city_controller
        )
        self._calc_tabs.addTab(self._transit_panel, "Транзиты")
        
        # Progression panel
        self._progression_panel = ProgressionPanel()
        self._calc_tabs.addTab(self._progression_panel, "Прогрессии")
        
        right_layout.addWidget(self._calc_tabs)
        
        # Add three panes to splitter: Left | Center (Chart) | Right
        self._main_splitter.addWidget(left_panel)
        self._main_splitter.addWidget(self._chart_view)
        self._main_splitter.addWidget(right_panel)
        
        # Set splitter sizes: Left 25%, Center 50%, Right 25%
        self._main_splitter.setSizes([350, 700, 350])
        
        # Transit state
        self._transit_available = False
        self._show_transits = True
        self._current_transit_mode = "calendar"
        self._current_transit_result = None
        
        # Initialize display profile editor as a dialog (will be shown on demand)
        self._display_profile_editor = DisplayProfileEditor(
            self._display_profile_controller
        )
        
    def _update_transit_chart_view(self, mode: str):
        """Calculate and display transit chart overlay on natal chart."""
        if not self._current_chart_result:
            return
            
        try:
            self._current_transit_mode = mode
            
            # Get transit data for current date/range
            if mode == "calendar":
                # For calendar mode, use the transit date
                transit_date = self._transit_panel.edit_transit_date.date().toPyDate()
                start_date = transit_date
                end_date = transit_date
            elif mode == "precise":
                transit_date = self._transit_panel.edit_transit_date.date().toPyDate()
                start_date = transit_date
                end_date = transit_date
            else:  # periods
                start_date = self._transit_panel.edit_start_date.date().toPyDate()
                end_date = self._transit_panel.edit_end_date.date().toPyDate()
            
            # Calculate transits for chart
            transit_result = self._transit_controller.calculate_transits(
                natal_objects=self._current_chart_result.get("objects", []),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                settings=self._transit_controller.get_default_settings(),
                mode=mode,
                filter_planets=None,
                filter_aspects=None,
                display_profile_name=self._current_display_profile_name
            )
            
            self._current_transit_result = transit_result
            
            # Get transit planets and aspects for chart rendering
            transit_planets = self._extract_transit_planets_for_chart(transit_result, start_date, end_date)
            transit_aspects = self._extract_transit_aspects_for_chart(transit_result)
            
        # Render transit chart using new ChartPainter
        display_settings = self._get_display_settings()
        self._chart_view.set_transit_chart_data(
            natal_chart=self._current_chart_result,
            transit_planets=transit_planets,
            transit_aspects=transit_aspects,
            display_settings=display_settings
        )
        self._chart_view.set_transit_data(transit_planets, transit_aspects)
            
        except Exception as e:
        self._status_label.setText(f"Ошибка отображения транзитов: {str(e)}")
    
    def _extract_transit_planets_for_chart(self, transit_result, start_date, end_date):
        """Extract transit planets for chart rendering."""
        # For chart rendering, we need current positions of transit planets
        # This is a simplified version - in reality you'd calculate exact positions
        transit_planets = []
        seen_planets = set()
        
        for event in transit_result:
            planet_name = event.get("transit_planet", "")
            if planet_name and planet_name not in seen_planets:
                transit_planets.append({
                    "name": planet_name,
                    "longitude": event.get("transit_longitude", 0),
                    "sign": event.get("transit_sign", ""),
                    "retrograde": event.get("retrograde", False),
                    "speed_longitude": event.get("speed", 0)
                })
                seen_planets.add(planet_name)
        
        return transit_planets
    
    def _extract_transit_aspects_for_chart(self, transit_result):
        """Extract transit aspects for chart rendering."""
        transit_aspects = []
        for event in transit_result:
            transit_aspects.append({
                "transit_planet": event.get("transit_planet", ""),
                "natal_point": event.get("natal_point", ""),
                "aspect": event.get("aspect", ""),
                "orb": event.get("orb", 0),
                "angle": event.get("angle", 0)
            })
        return transit_aspects
        
    def _init_menus(self):
        """Initialize the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Файл")
        
        new_profile_action = QAction("&Новый профиль", self)
        new_profile_action.setShortcut(QKeySequence.StandardKey.New)
        new_profile_action.triggered.connect(self._on_new_profile)
        file_menu.addAction(new_profile_action)
        
        load_profile_action = QAction("&Загрузить профиль...", self)
        load_profile_action.setShortcut(QKeySequence.StandardKey.Open)
        load_profile_action.triggered.connect(self._on_load_profile)
        file_menu.addAction(load_profile_action)
        
        save_profile_action = QAction("&Сохранить профиль", self)
        save_profile_action.setShortcut(QKeySequence.StandardKey.Save)
        save_profile_action.triggered.connect(self._on_save_profile)
        file_menu.addAction(save_profile_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Calculations menu
        calc_menu = menubar.addMenu("&Расчёты")
        
        calculate_chart_action = QAction("&Рассчитать карту", self)
        calculate_chart_action.setShortcut("F5")
        calculate_chart_action.triggered.connect(self._on_calculate_chart)
        calc_menu.addAction(calculate_chart_action)
        
        calculate_transits_action = QAction("Рассчитать &транзиты", self)
        calculate_transits_action.setShortcut("F6")
        calculate_transits_action.triggered.connect(self._on_calculate_transits)
        calc_menu.addAction(calculate_transits_action)
        
        calculate_progressions_action = QAction("Рассчитать &прогрессии", self)
        calculate_progressions_action.setShortcut("F7")
        calculate_progressions_action.triggered.connect(self._on_calculate_progressions)
        calc_menu.addAction(calculate_progressions_action)
        
        calc_menu.addSeparator()
        
        clear_results_action = QAction("Очистить &результаты", self)
        clear_results_action.triggered.connect(self._on_clear_results)
        calc_menu.addAction(clear_results_action)
        
        # Profiles menu
        profiles_menu = menubar.addMenu("&Профили")
        
        manage_profiles_action = QAction("Управление профилями рождения...", self)
        manage_profiles_action.triggered.connect(self._on_manage_profiles)
        profiles_menu.addAction(manage_profiles_action)
        
        manage_display_profiles_action = QAction("Управление профилями отображения...", self)
        manage_display_profiles_action.triggered.connect(self._on_manage_display_profiles)
        profiles_menu.addAction(manage_display_profiles_action)
        
        # Display menu
        display_menu = menubar.addMenu("&Отображение")
        
        zoom_in_action = QAction("Увеличить &масштаб", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._chart_view.zoom_in)
        display_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Уменьшить &масштаб", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._chart_view.zoom_out)
        display_menu.addAction(zoom_out_action)
        
        reset_view_action = QAction("Сбросить &вид", self)
        reset_view_action.setShortcut("0")
        reset_view_action.triggered.connect(self._chart_view.reset_view)
        display_menu.addAction(reset_view_action)
        
        display_menu.addSeparator()
        
        # Transit toggle
        self._transit_toggle_action = QAction("Показать транзиты на карте", self)
        self._transit_toggle_action.setCheckable(True)
        self._transit_toggle_action.setChecked(True)
        self._transit_toggle_action.setEnabled(False)
        self._transit_toggle_action.triggered.connect(self._toggle_transits)
        display_menu.addAction(self._transit_toggle_action)
        
        display_menu.addSeparator()
        
        # Panel visibility
        self._toggle_left_panel_action = QAction("Скрыть/показать левую панель", self)
        self._toggle_left_panel_action.setShortcut("Ctrl+L")
        self._toggle_left_panel_action.triggered.connect(self._toggle_left_panel)
        display_menu.addAction(self._toggle_left_panel_action)
        
        self._toggle_right_panel_action = QAction("Скрыть/показать правую панель", self)
        self._toggle_right_panel_action.setShortcut("Ctrl+R")
        self._toggle_right_panel_action.triggered.connect(self._toggle_right_panel)
        display_menu.addAction(self._toggle_right_panel_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Помощь")
        
        about_action = QAction("&О программе", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
        
    def _init_toolbars(self):
        """Initialize toolbars."""
        # Main toolbar
        toolbar = QToolBar("Основная панель инструментов")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Calculate chart button
        calc_chart_action = QAction("🔮 Рассчитать карту", self)
        calc_chart_action.setToolTip("Рассчитать натальную карту (F5)")
        calc_chart_action.triggered.connect(self._on_calculate_chart)
        toolbar.addAction(calc_chart_action)
        
        toolbar.addSeparator()
        
        # Calculate transits button
        calc_transits_action = QAction("📊 Транзиты", self)
        calc_transits_action.setToolTip("Рассчитать транзиты (F6)")
        calc_transits_action.triggered.connect(self._on_calculate_transits)
        toolbar.addAction(calc_transits_action)
        
        # Calculate progressions button
        calc_progressions_action = QAction("📈 Прогрессии", self)
        calc_progressions_action.setToolTip("Рассчитать прогрессии (F7)")
        calc_progressions_action.triggered.connect(self._on_calculate_progressions)
        toolbar.addAction(calc_progressions_action)
        
        toolbar.addSeparator()
        
        # Profile buttons
        load_profile_action = QAction("📂 Загрузить профиль", self)
        load_profile_action.setToolTip("Загрузить профиль рождения")
        load_profile_action.triggered.connect(self._on_load_profile)
        toolbar.addAction(load_profile_action)
        
        save_profile_action = QAction("💾 Сохранить профиль", self)
        save_profile_action.setToolTip("Сохранить профиль рождения")
        save_profile_action.triggered.connect(self._on_save_profile)
        toolbar.addAction(save_profile_action)
        
        toolbar.addSeparator()
        
        # Display profile editor
        edit_display_action = QAction("🎨 Редактор профилей", self)
        edit_display_action.setToolTip("Редактировать профиль отображения")
        edit_display_action.triggered.connect(self._on_edit_display_profile)
        toolbar.addAction(edit_display_action)
        
        toolbar.addSeparator()
        
        # Transit toggle
        self._toolbar_transit_toggle = QAction("📊 Транзиты на карте", self)
        self._toolbar_transit_toggle.setCheckable(True)
        self._toolbar_transit_toggle.setChecked(True)
        self._toolbar_transit_toggle.setEnabled(False)
        self._toolbar_transit_toggle.setToolTip("Показать/скрыть транзиты на натальной карте")
        self._toolbar_transit_toggle.triggered.connect(self._toggle_transits)
        toolbar.addAction(self._toolbar_transit_toggle)
        
        toolbar.addSeparator()
        
        # Panel visibility toggles
        toggle_left_action = QAction("📋 Левая панель", self)
        toggle_left_action.setCheckable(True)
        toggle_left_action.setChecked(True)
        toggle_left_action.setToolTip("Скрыть/показать левую панель (Ctrl+L)")
        toggle_left_action.triggered.connect(self._toggle_left_panel)
        toolbar.addAction(toggle_left_action)
        
        toggle_right_action = QAction("📋 Правая панель", self)
        toggle_right_action.setCheckable(True)
        toggle_right_action.setChecked(True)
        toggle_right_action.setToolTip("Скрыть/показать правую панель (Ctrl+R)")
        toggle_right_action.triggered.connect(self._toggle_right_panel)
        toolbar.addAction(toggle_right_action)
        
    def _init_status_bar(self):
        """Initialize status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        # Status label
        self._status_label = QLabel("Готово")
        self._status_bar.addWidget(self._status_label)
        
        # Progress bar (hidden by default)
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._status_bar.addPermanentWidget(self._progress_bar)
        
        # Coordinates display
        self._coords_label = QLabel("")
        self._status_bar.addPermanentWidget(self._coords_label)
        
    def _connect_signals(self):
        """Connect widget signals to slots."""
        # Birth input panel signals
        self._birth_input_panel.calculate_requested.connect(self._handle_calculate_chart)
        self._birth_input_panel.profile_load_requested.connect(self._on_load_profile_from_input)
        self._birth_input_panel.profile_save_requested.connect(self._on_save_profile_from_input)
        self._birth_input_panel.profile_edit_requested.connect(self._on_edit_profile_from_input)
        self._birth_input_panel.profile_delete_requested.connect(self._on_delete_profile_from_input)
        self._birth_input_panel.display_profile_apply_requested.connect(self._on_apply_display_profile)
        self._birth_input_panel.display_profile_save_requested.connect(self._on_save_display_profile)
        self._birth_input_panel.recalc_triggered.connect(self._on_recalculate_chart)
        
        # Transit panel signals
        self._transit_panel.calculate_requested.connect(self._handle_calculate_transits)
        
        # Progression panel signals
        self._progression_panel.calculate_requested.connect(self._handle_calculate_progressions)
        
        # Profile manager signals
        self._profile_manager.profile_selected.connect(self._on_profile_selected)
        self._profile_manager.profile_deleted.connect(self._on_profile_deleted)
        self._profile_manager.profile_edited.connect(self._on_profile_edited)
        
        # Chart view signals
        self._chart_view.chart_clicked.connect(self._on_chart_clicked)
        
    def _load_state(self):
        """Load application state."""
        state = self._state_manager.state
        
        # Restore UI state
        self._show_left_panel = state.show_left_panel
        self._show_right_panel = state.show_right_panel
        self._current_tab_index = state.current_tab
        
        # Restore display profile
        self._current_display_profile_name = state.display_profile_name

        # Синхронизировать выпадающий список профилей отображения
        # с восстановленным состоянием, чтобы расчёт карты
        # использовал тот же профиль, что и состояние приложения.
        if hasattr(self, '_birth_input_panel'):
            self._birth_input_panel.combo_display_profile.setCurrentText(
                self._current_display_profile_name
            )
        
        # Apply display profile to chart view settings
        self._update_chart_view_settings()

    def _get_display_settings(self) -> dict:
        """Получает текущие настройки отображения."""
        try:
            from astro_core.display_profiles import load_display_profile, get_render_kwargs
            
            if self._current_display_profile_name:
                profile = load_display_profile(self._current_display_profile_name)
                return get_render_kwargs(profile)
        except Exception:
            pass
        
        # Настройки по умолчанию
        return {
            "show_planet_labels": True,
            "show_asteroid_labels": True,
            "show_node_labels": True,
            "show_angle_labels": True,
            "show_houses": True,
            "show_aspects": True,
            "label_mode": "symbols",
        }
        
    def _save_state(self):
        """Save application state."""
        state = self._state_manager.state
        state.show_left_panel = self._show_left_panel
        state.show_right_panel = self._show_right_panel
        state.current_tab = self._current_tab_index
        state.display_profile_name = self._current_display_profile_name
        self._state_manager.mark_dirty()
        self._state_manager.save()
        
        def _update_chart_view(self):
        """Update the chart view with current chart result."""
        if self._current_chart_result:
            try:
                # Получаем настройки отображения
                display_settings = self._get_display_settings()
                
                # Используем новый метод отрисовки
                self._chart_view.set_chart_data(
                    self._current_chart_result,
                    display_settings
                )
                
                # Сохраняем SVG для экспорта (если есть)
                svg_content = self._current_chart_result.get("svg", "")
                if svg_content:
                    self._chart_view.set_svg(svg_content)
                
                # Обновляем статус
                chart_type = self._current_chart_result.get("chart_type", "Натальная карта")
                self._status_label.setText(f"{chart_type} - {self._current_birth_data.get('name', 'Chart') if self._current_birth_data else ''}")
            except Exception as e:
                self._status_label.setText(f"Ошибка отображения карты: {str(e)}")
        else:
            # Очищаем вид
            self._chart_view._scene.clear()
            self._chart_view._scene.addText("Введите данные и нажмите 'Рассчитать карту'")
            self._status_label.setText("Готово")
    
    def _get_display_settings(self) -> Dict:
        """Получает текущие настройки отображения."""
        try:
            from astro_core.display_profiles import load_display_profile, get_render_kwargs
            
            if self._current_display_profile_name:
                profile = load_display_profile(self._current_display_profile_name)
                return get_render_kwargs(profile)
        except Exception:
            pass
        
        # Настройки по умолчанию
        return {
            "show_planet_labels": True,
            "show_asteroid_labels": True,
            "show_node_labels": True,
            "show_angle_labels": True,
            "show_houses": True,
            "show_aspects": True,
            "label_mode": "symbols",
        }
            
    def _set_left_panel_visible(self, visible: bool):
        """Show or hide left panel."""
        if hasattr(self, '_main_splitter'):
            widget = self._main_splitter.widget(0)  # Left panel
            if widget:
                widget.setVisible(visible)
                self._show_left_panel = visible
                self._save_state()
                
    def _set_right_panel_visible(self, visible: bool):
        """Show or hide right panel."""
        if hasattr(self, '_main_splitter'):
            widget = self._main_splitter.widget(1)  # Right panel
            if widget:
                widget.setVisible(visible)
                self._show_right_panel = visible
                self._save_state()
                
    # ============================================================
    # Menu and Toolbar Slots
    # ============================================================
    
    def _on_new_profile(self):
        """Handle new profile action."""
        self._birth_input_panel.clear_editing_profile()
        self._birth_input_panel.setFocus()
        
    def _on_load_profile(self):
        """Handle load profile action."""
        name, ok = self._get_profile_name_for_action("Загрузить профиль")
        if ok and name:
            self._load_profile(name)
            
    def _on_save_profile(self):
        """Handle save profile action."""
        self._save_profile(None)  # Save current profile as new
        
    def _on_load_profile_from_input(self, profile_name: str):
        """Handle load profile request from birth input panel."""
        self._load_profile(profile_name)
        
    def _on_save_profile_from_input(self, editing_name: Optional[str]):
        """Handle save profile request from birth input panel."""
        self._save_profile(editing_name)
        
    def _on_edit_profile_from_input(self, profile_name: str):
        """Handle edit profile request from birth input panel."""
        self._edit_profile(profile_name)
        
    def _on_delete_profile_from_input(self, profile_name: str):
        """Handle delete profile request from birth input panel."""
        self._delete_profile(profile_name)
        
    def _on_apply_display_profile(self, profile_name: str):
        """Handle apply display profile request."""
        self._apply_display_profile(profile_name)
        
    def _on_save_display_profile(self, profile_name: str):
        """Handle save display profile request."""
        self._save_display_profile(profile_name)
        
    def _on_calculate_chart(self):
        """Handle calculate chart action."""
        self._birth_input_panel._on_calculate()
        
    def _on_calculate_transits(self):
        """Handle calculate transits action."""
        self._transit_panel._on_calculate()
        
    def _on_calculate_progressions(self):
        """Handle calculate progressions action."""
        self._progression_panel._on_calculate()
        
    def _on_clear_results(self):
        """Handle clear results action."""
        self._current_chart_result = None
        self._current_birth_data = None
        self._chart_view._scene.clear()
        self._chart_view._scene.addText("Введите данные и нажмите 'Рассчитать карту'")
        self._transit_panel.table_results.setRowCount(0)
        self._progression_panel.table_planets.setRowCount(0)
        self._progression_panel.table_points.setRowCount(0)
        self._progression_panel.table_aspects.setRowCount(0)
        self._status_label.setText("Результаты очищены")
        self._save_state()
        
    def _on_manage_profiles(self):
        """Handle manage profiles action."""
        # Toggle profile manager visibility
        self._profile_manager.setVisible(not self._profile_manager.isVisible())
        
    def _on_manage_display_profiles(self):
        """Handle manage display profiles action."""
        self._display_profile_editor.show()
        
    def _on_edit_display_profile(self):
        """Handle edit display profile action."""
        self._display_profile_editor.show()
        
    def _on_about(self):
        """Handle about action."""
        QMessageBox.about(
            self,
            "О Astro Processor",
            "Astro Processor v1.0\n\n"
            "Модульный астрологический процессор с поддержкой:\n"
            "• Натальных карт\n"
            "• Транзитов (3 режима)\n"
            "• Прогрессий (вторичные и солнечная дуга)\n"
            "• Профилей рождения и отображения\n"
            "• Графических SVG-карт с зумом/панорамированием\n\n"
            "© 2026 Astro Processor Project"
        )
        
    def _on_recalculate_chart(self):
        """Handle recalculate chart trigger."""
        if self._current_birth_data and self._current_chart_result:
            self._on_calculate_chart()
            
    def _update_transit_toggle_visibility(self):
        """Update transit toggle visibility based on transit availability."""
        enabled = getattr(self, '_transit_available', False)
        if hasattr(self, '_transit_toggle_action'):
            self._transit_toggle_action.setEnabled(enabled)
        if hasattr(self, '_toolbar_transit_toggle'):
            self._toolbar_transit_toggle.setEnabled(enabled)
    
    def _toggle_transits(self, checked: bool):
        """Toggle transit display on chart."""
        self._show_transits = checked
        if hasattr(self, '_transit_toggle_action'):
            self._transit_toggle_action.setChecked(checked)
        if hasattr(self, '_toolbar_transit_toggle'):
            self._toolbar_transit_toggle.setChecked(checked)
        
        # Update chart view
        if self._current_chart_result and self._current_transit_result:
            if checked:
                # Show transit chart
                self._update_transit_chart_view(self._current_transit_mode)
            else:
                # Show natal chart only
                self._update_chart_view()
        
        self._save_state()
    
    def _toggle_left_panel(self, checked: bool = None):
        """Toggle left panel visibility."""
        if hasattr(self, '_main_splitter'):
            widget = self._main_splitter.widget(0)  # Left panel
            if widget:
                if checked is None:
                    checked = not widget.isVisible()
                widget.setVisible(checked)
                if hasattr(self, '_toggle_left_panel_action'):
                    self._toggle_left_panel_action.setChecked(checked)
                self._save_state()
    
    def _toggle_right_panel(self, checked: bool = None):
        """Toggle right panel visibility."""
        if hasattr(self, '_main_splitter'):
            widget = self._main_splitter.widget(2)  # Right panel (index 2 in 3-pane layout)
            if widget:
                if checked is None:
                    checked = not widget.isVisible()
                widget.setVisible(checked)
                if hasattr(self, '_toggle_right_panel_action'):
                    self._toggle_right_panel_action.setChecked(checked)
                self._save_state()
    
    def _on_recalculate_chart(self):
        """Handle recalculate chart trigger."""
        if self._current_birth_data and self._current_chart_result:
            self._on_calculate_chart()
            
    # ============================================================
    # Calculation Handler Methods
    # ============================================================
    
    def _handle_calculate_chart(self, birth_data: dict, settings: dict, display_profile_name: str):
        """Handle chart calculation request."""
        self._show_progress("Расчёт натальной карты...")
        
        try:
            # Store current data
            self._current_birth_data = birth_data
            self._current_display_profile_name = display_profile_name
            
            # Calculate chart
            result = self._chart_controller.calculate_chart(
                birth_data,
                settings,
                display_profile_name,
                include_svg=True
            )
            
            self._current_chart_result = result
            
            # Update chart view
            self._update_chart_view()
            
            # Clear transit/progression results
            self._transit_panel.table_results.setRowCount(0)
            self._progression_panel.table_planets.setRowCount(0)
            self._progression_panel.table_points.setRowCount(0)
            self._progression_panel.table_aspects.setRowCount(0)
            
            # Update transit panel with natal data for calculations
            natal_objects = result.get("objects", [])
            chart_settings = result.get("settings", {})
            self._transit_panel.set_natal_data(natal_objects, chart_settings)
            
            self._hide_progress()
            self._status_label.setText(f"Карта рассчитана: {birth_data.get('name', 'Chart')}")
            self._save_state()
            
        except Exception as e:
            self._hide_progress()
            QMessageBox.critical(self, "Ошибка расчёта", f"Не удалось рассчитать карту:\n{str(e)}")
            self._status_label.setText("Ошибка расчёта карты")
            
    def _handle_calculate_transits(self, mode: str, start_date, end_date, planets: list, aspects: list):
        """Handle transit calculation request."""
        if not self._current_chart_result:
            QMessageBox.warning(self, "Предупреждение", "Сначала рассчитайте натальную карту")
            return
            
        self._show_progress("Расчёт транзитов...")
        
        try:
            # Calculate transits
            result = self._transit_controller.calculate_transits(
                natal_objects=self._current_chart_result.get("objects", []),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                settings=self._transit_controller.get_default_settings(),
                mode=mode,
                filter_planets=planets if planets else None,
                filter_aspects=aspects if aspects else None,
                display_profile_name=self._current_display_profile_name
            )
            
            # Display results in table
            self._transit_panel.set_results(result)
            
            # Calculate and display transit chart overlay
            if mode in ["calendar", "precise", "periods"]:
                self._update_transit_chart_view(mode)
            
            # Enable transit toggle
            self._transit_available = True
            self._update_transit_toggle_visibility()
            
            self._hide_progress()
            self._status_label.setText(f"Транзиты рассчитаны: {len(result)} записей")
            self._save_state()
            
        except Exception as e:
            self._hide_progress()
            QMessageBox.critical(self, "Ошибка расчёта транзитов", f"Не удалось рассчитать транзиты:\n{str(e)}")
            self._status_label.setText("Ошибка расчёта транзитов")
            
    def _handle_calculate_progressions(self, progression_type: str, progression_date):
        """Handle progression calculation request."""
        if not self._current_chart_result:
            QMessageBox.warning(self, "Предупреждение", "Сначала рассчитайте натальную карту")
            return
            
        self._show_progress("Расчёт прогрессий...")
        
        try:
            # Calculate progressions
            result = self._progression_controller.calculate_progressions(
                birth_data=self._current_birth_data,
                progression_date=progression_date,
                progression_type=progression_type,
                display_profile_name=self._current_display_profile_name
            )
            
            # Display results in tables
            self._progression_panel.set_results(result)
            
            self._hide_progress()
            self._status_label.setText(f"Прогрессии рассчитаны: {progression_type} на {progression_date}")
            self._save_state()
            
        except Exception as e:
            self._hide_progress()
            QMessageBox.critical(self, "Ошибка расчёта прогрессий", f"Не удалось рассчитать прогрессии:\n{str(e)}")
            self._status_label.setText("Ошибка расчёта прогрессий")
            
    # ============================================================
    # Profile Management Methods
    # ============================================================
    
    def _load_profile(self, profile_name: str):
        """Load a birth profile."""
        try:
            profile = self._profile_controller.load_profile(profile_name)
            
            # Update birth input panel with profile data
            birth_data = self._profile_controller.profile_to_birth_data(profile)
            self._birth_input_panel.set_birth_data(birth_data)
            
            # Set profile as current
            self._profile_controller.set_current_profile(profile)
            
            self._status_label.setText(f"Профиль загружен: {profile_name}")
            self._save_state()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка загрузки профиля", f"Не удалось загрузить профиль:\n{str(e)}")
            
    def _save_profile(self, editing_name: Optional[str] = None):
        """Save a birth profile."""
        try:
            # Get data from birth input panel
            birth_data = self._birth_input_panel.get_birth_data()
            
            # Create profile
            from datetime import datetime
            from astro_core.controllers.profile_controller import BirthProfile
            
            profile = BirthProfile(
                name=birth_data["name"],
                birth_date=datetime.strptime(birth_data["date"], "%Y-%m-%d").date(),
                birth_time=datetime.strptime(birth_data["time"], "%H:%M").time(),
                latitude=birth_data["latitude"],
                longitude=birth_data["longitude"],
                utc_offset_hours=birth_data["utc_offset_hours"],
                timezone="",  # Will be filled by controller if needed
                created_at=datetime.now().isoformat() if not editing_name else None
            )
            
            # Validate
            errors = self._profile_controller.validate_profile(profile)
            if errors:
                QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
                return
                
            # Save profile
            saved_path = self._profile_controller.save_profile(profile)
            
            # If editing, delete old profile if name changed
            if editing_name and profile.name != editing_name:
                self._profile_controller.delete_profile(editing_name)
                
            self._status_label.setText(f"Профиль сохранен: {profile.name}")
            self._save_state()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка сохранения профиля", f"Не удалось сохранить профиль:\n{str(e)}")
            
    def _edit_profile(self, profile_name: str):
        """Edit a birth profile."""
        self._load_profile(profile_name)
        self._birth_input_panel.set_editing_profile(profile_name)
        
    def _delete_profile(self, profile_name: str):
        """Delete a birth profile."""
        reply = QMessageBox.question(
            self,
            "Удалить профиль",
            f"Удалить профиль '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._profile_controller.delete_profile(profile_name)
                self._status_label.setText(f"Профиль удален: {profile_name}")
                self._save_state()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка удаления профиля", f"Не удалось удалить профиль:\n{str(e)}")
                
    def _on_profile_selected(self, profile):
        """Handle profile selection from profile manager."""
        self._load_profile(profile.name)
        
    def _on_profile_deleted(self, profile_name: str):
        """Handle profile deletion from profile manager."""
        self._delete_profile(profile_name)
        
    def _on_profile_edited(self, profile_name: str):
        """Handle profile edit from profile manager."""
        self._edit_profile(profile_name)
        
    # ============================================================
    # Display Profile Methods
    # ============================================================
    
    def _apply_display_profile(self, profile_name: str):
        """Apply a display profile."""
        try:
            self._display_profile_controller.set_current_profile(profile_name)
            self._current_display_profile_name = profile_name
            
            # Update chart view with new appearance
            self._update_chart_view_settings()
            self._update_chart_view()  # Re-render with new profile
            
            self._status_label.setText(f"Профиль отображения применен: {profile_name}")
            self._save_state()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка применения профиля", f"Не удалось применить профиль отображения:\n{str(e)}")
            
    def _save_display_profile(self, profile_name: str):
        """Save a display profile."""
        try:
            # Collect data from display profile editor
            profile_data = self._display_profile_editor._collect_profile_data()
            profile_data["name"] = profile_name
            
            # Convert to DisplayProfile and save
            from astro_core.controllers.display_profile_controller import DisplayProfile
            profile = self._display_profile_controller._dict_to_profile(profile_data)
            
            # Validate
            errors = self._display_profile_controller.validate_profile(profile)
            if errors:
                QMessageBox.warning(self, "Ошибка валидации", "\n".join(errors))
                return
                
            # Save profile
            saved_path = self._display_profile_controller.save_profile(profile)
            
            self._status_label.setText(f"Профиль отображения сохранен: {profile_name}")
            self._save_state()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка сохранения профиля отображения", f"Не удалось сохранить профиль отображения:\n{str(e)}")
            
    # ============================================================
    # Helper Methods
    # ============================================================
    
    def _get_profile_name_for_action(self, action_text: str) -> tuple[str, bool]:
        """Get profile name from user via input dialog."""
        profile_names = self._profile_controller.get_profile_names()
        if not profile_names:
            QMessageBox.information(self, "Информация", "Нет сохраненных профилей")
            return "", False
            
        name, ok = QInputDialog.getItem(
            self,
            action_text,
            "Выберите профиль:",
            profile_names,
            0,
            False
        )
        return name, ok
        
    def _show_progress(self, message: str):
        """Show progress bar with message."""
        self._status_label.setText(message)
        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)  # Indeterminate progress
        
    def _hide_progress(self):
        """Hide progress bar."""
        self._progress_bar.setVisible(False)
        
    def _on_chart_clicked(self, scene_pos):
        """Handle chart click."""
        self._status_label.setText(f"Клик по карте: позиция сцены ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
        
    # ============================================================
    # Override Methods
    # ============================================================
    
    def closeEvent(self, event):
        """Handle window close event."""
        self._save_state()
        event.accept()