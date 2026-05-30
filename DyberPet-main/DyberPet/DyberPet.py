import sys
from sys import platform
import time
import math
import types
import random
import inspect
import webbrowser
import threading
from typing import List
from pathlib import Path
import pynput.mouse as mouse

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer, QObject, QPoint, QEvent, QElapsedTimer
from PySide6.QtCore import QObject, QThread, Signal, QRectF, QRect, QSize, QPropertyAnimation, QAbstractAnimation
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor, QPainter, QFont, QFontMetrics, QAction, QBrush, QPen, QColor, QFontDatabase, QPainterPath, QRegion, QIntValidator, QDoubleValidator

from qfluentwidgets import CaptionLabel, setFont, Action #,RoundMenu
from qfluentwidgets import FluentIcon as FIF
from DyberPet.custom_widgets import SystemTray
from .custom_roundmenu import RoundMenu

from DyberPet.conf import *
from DyberPet.utils import *
from DyberPet.modules import *
from DyberPet.Accessory import MouseMoveManager
from DyberPet.custom_widgets import RoundBarBase, LevelBadge
from DyberPet.bubbleManager import BubbleManager
from frontend.agent_client import AgentClient
from frontend.audio_recorder import AudioRecorder
from frontend.input_panel import InputPanel
from frontend.player_status_poller import PlayerStatusPoller
from frontend.state_mapper import map_agent_result, pick_action_for_state
from frontend.whisper_adapter import WhisperAdapter

# initialize settings
import DyberPet.settings as settings
settings.init()

basedir = settings.BASEDIR
configdir = settings.CONFIGDIR


# version
dyberpet_version = settings.VERSION
vf = open(os.path.join(configdir,'data/version'), 'w')
vf.write(dyberpet_version)
vf.close()

# some UI size parameters
status_margin = int(3)
statbar_h = int(20)
icons_wh = 20

# system config
sys_hp_tiers = settings.HP_TIERS 
sys_hp_interval = settings.HP_INTERVAL
sys_lvl_bar = settings.LVL_BAR
sys_pp_heart = settings.PP_HEART
sys_pp_item = settings.PP_ITEM
sys_pp_audio = settings.PP_AUDIO


# Pet HP progress bar
class DP_HpBar(QProgressBar):
    hptier_changed = Signal(int, str, name='hptier_changed')
    hp_updated = Signal(int, name='hp_updated')

    def __init__(self, *args, **kwargs):

        super(DP_HpBar, self).__init__(*args, **kwargs)

        self.setFormat('0/100')
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)
        self.hp_tiers = sys_hp_tiers #[0,50,80,100]

        self.hp_max = 100
        self.interval = 1
        self.hp_inner = 0
        self.hp_perct = 0

        # Custom colors and sizes
        self.bar_color = QColor("#FAC486")  # Fill color
        self.border_color = QColor(0, 0, 0) # Border color
        self.border_width = 1               # Border width in pixels
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Full widget rect minus border width to avoid overlap
        full_rect = QRectF(self.border_width / 2.0, self.border_width / 2.0,
                           self.width() - self.border_width, self.height() - self.border_width)
        radius = (self.height() - self.border_width) / 2.0

        # Draw the background rounded rectangle
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Light gray background
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawRoundedRect(full_rect, radius, radius)

        # Create a clipping path for the filled progress that is inset by the border width
        clip_path = QPainterPath()
        inner_rect = full_rect.adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        clip_path.addRoundedRect(inner_rect, radius - self.border_width, radius - self.border_width)
        painter.setClipPath(clip_path)

        # Calculate progress rect and draw it within the clipping region
        progress_width = (self.width() - 2 * self.border_width) * self.value() / self.maximum()
        progress_rect = QRectF(self.border_width, self.border_width,
                               progress_width, self.height() - 2 * self.border_width)

        painter.setBrush(QBrush(self.bar_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(progress_rect)
        
        # Text drawing
        painter.setClipping(False)  # Disable clipping to draw text over entire bar
        text = self.format()  # Use the format string directly
        painter.setPen(QColor(0, 0, 0))  # Set text color
        font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font)
        #painter.drawText(full_rect, Qt.AlignCenter, text)
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        # Draw text in the calculated position
        painter.drawText(full_rect.adjusted(0, -font_metrics.descent()//2, 0, 0), Qt.AlignCenter, text)

    def init_HP(self, change_value, interval_time):
        self.hp_max = int(100*interval_time)
        self.interval = interval_time
        if change_value == -1:
            self.hp_inner = self.hp_max
            settings.pet_data.change_hp(self.hp_inner)
        else:
            self.hp_inner = change_value
        self.hp_perct = math.ceil(round(self.hp_inner/self.interval, 1))
        self.setFormat('%i/100'%self.hp_perct)
        self.setValue(self.hp_perct)
        self._onTierChanged()
        self.hp_updated.emit(self.hp_perct)

    def updateValue(self, change_value, from_mod):

        before_value = self.value()

        if from_mod == 'Scheduler':
            if settings.HP_stop:
                return
            new_hp_inner = max(self.hp_inner + change_value, 0)

        else:

            if change_value > 0:
                new_hp_inner = min(self.hp_inner + change_value*self.interval, self.hp_max)

            elif change_value < 0:
                new_hp_inner = max(self.hp_inner + change_value*self.interval, 0)

            else:
                return 0


        if new_hp_inner == self.hp_inner:
            return 0
        else:
            self.hp_inner = new_hp_inner

        new_hp_perct = math.ceil(round(self.hp_inner/self.interval, 1))
            
        if new_hp_perct == self.hp_perct:
            settings.pet_data.change_hp(self.hp_inner)
            return 0
        else:
            self.hp_perct = new_hp_perct
            self.setFormat('%i/100'%self.hp_perct)
            self.setValue(self.hp_perct)
        
        after_value = self.value()

        hp_tier = sum([int(after_value>i) for i in self.hp_tiers])

        #告知动画模块、通知模块
        if hp_tier > settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'up')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            self._onTierChanged()

        elif hp_tier < settings.pet_data.hp_tier:
            self.hptier_changed.emit(hp_tier,'down')
            settings.pet_data.change_hp(self.hp_inner, hp_tier)
            self._onTierChanged()
            
        else:
            settings.pet_data.change_hp(self.hp_inner) #.hp = current_value

        self.hp_updated.emit(self.hp_perct)
        return int(after_value - before_value)

    def _onTierChanged(self):
        colors = ["#f8595f", "#f8595f", "#FAC486", "#abf1b7"]
        self.bar_color = QColor(colors[settings.pet_data.hp_tier])  # Fill color
        self.update()
        



# Favorability Progress Bar
class DP_FvBar(QProgressBar):
    fvlvl_changed = Signal(int, name='fvlvl_changed')
    fv_updated = Signal(int, int, name='fv_updated')

    def __init__(self, *args, **kwargs):

        super(DP_FvBar, self).__init__(*args, **kwargs)

        # Custom colors and sizes
        self.bar_color = QColor("#F4665C")  # Fill color
        self.border_color = QColor(0, 0, 0) # Border color
        self.border_width = 1               # Border width in pixels

        self.fvlvl = 0
        self.lvl_bar = sys_lvl_bar #[20, 120, 300, 600, 1200]
        self.points_to_lvlup = self.lvl_bar[self.fvlvl]
        self.setMinimum(0)
        self.setMaximum(self.points_to_lvlup)
        self.setFormat('lv%s: 0/%s'%(int(self.fvlvl), self.points_to_lvlup))
        self.setValue(0)
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Full widget rect minus border width to avoid overlap
        full_rect = QRectF(self.border_width / 2.0, self.border_width / 2.0,
                           self.width() - self.border_width, self.height() - self.border_width)
        radius = (self.height() - self.border_width) / 2.0

        # Draw the background rounded rectangle
        painter.setBrush(QBrush(QColor(240, 240, 240)))  # Light gray background
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawRoundedRect(full_rect, radius, radius)

        # Create a clipping path for the filled progress that is inset by the border width
        clip_path = QPainterPath()
        inner_rect = full_rect.adjusted(self.border_width, self.border_width, -self.border_width, -self.border_width)
        clip_path.addRoundedRect(inner_rect, radius - self.border_width, radius - self.border_width)
        painter.setClipPath(clip_path)

        # Calculate progress rect and draw it within the clipping region
        progress_width = (self.width() - 2 * self.border_width) * self.value() / self.maximum()
        progress_rect = QRectF(self.border_width, self.border_width,
                               progress_width, self.height() - 2 * self.border_width)

        painter.setBrush(QBrush(self.bar_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(progress_rect)
        
        # Text drawing
        painter.setClipping(False)  # Disable clipping to draw text over entire bar
        text = self.format()  # Use the format string directly
        painter.setPen(QColor(0, 0, 0))  # Set text color
        font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(font)
        #painter.drawText(full_rect, Qt.AlignCenter, text)
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        # Draw text in the calculated position
        painter.drawText(full_rect.adjusted(0, -font_metrics.descent()//2, 0, 0), Qt.AlignCenter, text)

    def init_FV(self, fv_value, fv_lvl):
        self.fvlvl = fv_lvl
        self.points_to_lvlup = self.lvl_bar[self.fvlvl]
        self.setMinimum(0)
        self.setMaximum(self.points_to_lvlup)
        self.setFormat('lv%s: %i/%s'%(int(self.fvlvl), fv_value, self.points_to_lvlup))
        self.setValue(fv_value)
        self.fv_updated.emit(self.value(), self.fvlvl)

    def updateValue(self, change_value, from_mod):

        before_value = self.value()

        if from_mod == 'Scheduler':
            if settings.pet_data.hp_tier > 1:
                prev_value = self.value()
                current_value = self.value() + change_value #, self.maximum())
            elif settings.pet_data.hp_tier == 0 and not settings.FV_stop:
                prev_value = self.value()
                current_value = self.value() - 1
            else:
                return 0

        elif change_value != 0:
            prev_value = self.value()
            current_value = self.value() + change_value

        else:
            return 0


        if current_value < self.maximum():
            self.setValue(current_value)

            current_value = self.value()
            if current_value == prev_value:
                return 0
            else:
                self.setFormat('lv%s: %s/%s'%(int(self.fvlvl), int(current_value), int(self.maximum())))
                settings.pet_data.change_fv(current_value)
            after_value = self.value()

            self.fv_updated.emit(self.value(), self.fvlvl)
            return int(after_value - before_value)

        else: #好感度升级
            addedValue = self._level_up(current_value, prev_value)
            self.fv_updated.emit(self.value(), self.fvlvl)
            return addedValue

    def _level_up(self, newValue, oldValue, added=0):
        if self.fvlvl == (len(self.lvl_bar)-1):
            current_value = self.maximum()
            if current_value == oldValue:
                return 0
            self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(current_value),self.points_to_lvlup))
            self.setValue(current_value)
            settings.pet_data.change_fv(current_value, self.fvlvl)
            #告知动画模块、通知模块
            self.fvlvl_changed.emit(-1)
            return current_value - oldValue + added

        else:
            #after_value = newValue
            added_tmp = self.maximum() - oldValue
            newValue -= self.maximum()
            self.fvlvl += 1
            self.points_to_lvlup = self.lvl_bar[self.fvlvl]
            self.setMinimum(0)
            self.setMaximum(self.points_to_lvlup)
            self.setFormat('lv%s: %s/%s'%(int(self.fvlvl),int(newValue),self.points_to_lvlup))
            self.setValue(newValue)
            settings.pet_data.change_fv(newValue, self.fvlvl)
            #告知动画模块、通知模块
            self.fvlvl_changed.emit(self.fvlvl)

            if newValue < self.maximum():
                return newValue + added_tmp + added
            else:
                return self._level_up(newValue, 0, added_tmp)




# Pet Object
class PetWidget(QWidget):
    setup_notification = Signal(str, str, name='setup_notification')
    setup_bubbleText = Signal(dict, int, int, name="setup_bubbleText")
    close_bubble = Signal(str, name="close_bubble")
    addItem_toInven = Signal(int, list, name='addItem_toInven')
    fvlvl_changed_main_note = Signal(int, name='fvlvl_changed_main_note')
    fvlvl_changed_main_inve = Signal(int, name='fvlvl_changed_main_inve')
    hptier_changed_main_note = Signal(int, str, name='hptier_changed_main_note')

    setup_acc = Signal(dict, int, int, name='setup_acc')
    change_note = Signal(name='change_note')
    close_all_accs = Signal(name='close_all_accs')

    move_sig = Signal(int, int, name='move_sig')
    #acc_withdrawed = Signal(str, name='acc_withdrawed')
    send_positions = Signal(list, list, name='send_positions')

    lang_changed = Signal(name='lang_changed')
    show_controlPanel = Signal(name='show_controlPanel')

    show_dashboard = Signal(name='show_dashboard')
    hp_updated = Signal(int, name='hp_updated')
    fv_updated = Signal(int, int, name='fv_updated')

    compensate_rewards = Signal(name="compensate_rewards")
    refresh_bag = Signal(name="refresh_bag")
    addCoins = Signal(int, name='addCoins')
    autofeed = Signal(name='autofeed')

    stopAllThread = Signal(name='stopAllThread')

    taskUI_Timer_update = Signal(name="taskUI_Timer_update")
    taskUI_task_end = Signal(name="taskUI_task_end")
    single_pomo_done = Signal(name="single_pomo_done")

    refresh_acts = Signal(name='refresh_acts')
    agent_result_ready = Signal(dict, name='agent_result_ready')
    player_event_result_ready = Signal(str, name='player_event_result_ready')
    transcript_ready = Signal(str, name='transcript_ready')
    transcript_failed = Signal(str, name='transcript_failed')

    def __init__(self, parent=None, curr_pet_name=None, pets=(), screens=[]):
        """
        宠物组件
        :param parent: 父窗口
        :param curr_pet_name: 当前宠物名称
        :param pets: 全部宠物列表
        """
        super(PetWidget, self).__init__(parent) #, flags=Qt.WindowFlags())
        self.pets = settings.pets
        if curr_pet_name is None:
            self.curr_pet_name = settings.default_pet
        else:
            self.curr_pet_name = curr_pet_name
        #self.pet_conf = PetConfig()

        self.image = None
        self.tray = None
        self.agent_client = None
        self.input_panel = None
        self.whisper_adapter = None
        self.audio_recorder = None
        self.player_status_poller = None
        self.current_track = {}
        self.current_agent_state = "idle"
        self.current_player_status = "idle"
        self.current_pet_status_text = "待命中"
        self.last_user_text = ""

        # 鼠标拖拽初始属性
        self.is_follow_mouse = False
        self.mouse_moving = False
        self.mouse_drag_pos = self.pos()
        self.mouse_pos = [0, 0]

        # Record too frequent mouse clicking
        self.click_timer = QElapsedTimer()
        self.click_interval = 1000  # Max interval in ms to consider consecutive clicks
        self.click_count = 0

        # Screen info
        settings.screens = screens #[i.geometry() for i in screens]
        self.current_screen = settings.screens[0].availableGeometry() #geometry()
        settings.current_screen = settings.screens[0]
        #self.screen_geo = QDesktopWidget().availableGeometry() #screenGeometry()
        self.screen_width = self.current_screen.width() #self.screen_geo.width()
        self.screen_height = self.current_screen.height() #self.screen_geo.height()

        self._init_ui()
        self._init_widget()
        self.init_conf(self.curr_pet_name) # if curr_pet_name else self.pets[0])

        #self._set_menu(pets)
        #self._set_tray()
        self.show()

        self._setup_ui()
        self._init_echopet_frontend()

        # 开始动画模块和交互模块
        self.threads = {}
        self.workers = {}
        self.runAnimation()
        self.runInteraction()
        self.runScheduler()
        

        # 初始化重复提醒任务 - feature deleted
        #self.remind_window.initial_task()

        # 启动完毕10s后检查好感度等级奖励补偿
        self.compensate_timer = None
        self._setup_compensate()

    def _setup_compensate(self):
        self._stop_compensate()
        self.compensate_timer = QTimer(singleShot=True, timeout=self._compensate_rewards)
        self.compensate_timer.start(10000)

    def _stop_compensate(self):
        if self.compensate_timer:
            self.compensate_timer.stop()

    def moveEvent(self, event):
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def enterEvent(self, event):
        # Change the cursor when it enters the window
        self.setCursor(self.cursor_default)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Restore the original cursor when it leaves the window
        self.setCursor(self.cursor_user)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """
        鼠标点击事件
        :param event: 事件
        :return:
        """
        
        if event.button() == Qt.RightButton:
            # 打开右键菜单
            if settings.draging:
                return
            #self.setContextMenuPolicy(Qt.CustomContextMenu)
            #self.customContextMenuRequested.connect(self._show_Staus_menu)
            self._show_Staus_menu()
            
        if event.button() == Qt.LeftButton:
            # 左键绑定拖拽
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            
            if settings.onfloor == 0:
            # Left press activates Drag interaction
                if settings.set_fall:              
                    settings.onfloor=0
                settings.draging=1
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('mousedrag')
            
            # Record click
            if self.click_timer.isValid() and self.click_timer.elapsed() <= self.click_interval:
                self.click_count += 1
            else:
                self.click_count = 1
                self.click_timer.restart()
                
            event.accept()
            #self.setCursor(QCursor(Qt.ArrowCursor))
            self.setCursor(self.cursor_clicked)

    def mouseMoveEvent(self, event):
        """
        鼠标移动事件, 左键且绑定跟随, 移动窗体
        :param event:
        :return:
        """
        
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)

            self.mouse_moving = True
            self.setCursor(self.cursor_dragged)

            if settings.mouseposx3 == 0:
                
                settings.mouseposx1=QCursor.pos().x()
                settings.mouseposx2=settings.mouseposx1
                settings.mouseposx3=settings.mouseposx2
                settings.mouseposx4=settings.mouseposx3

                settings.mouseposy1=QCursor.pos().y()
                settings.mouseposy2=settings.mouseposy1
                settings.mouseposy3=settings.mouseposy2
                settings.mouseposy4=settings.mouseposy3
            else:
                #mouseposx5=mouseposx4
                settings.mouseposx4=settings.mouseposx3
                settings.mouseposx3=settings.mouseposx2
                settings.mouseposx2=settings.mouseposx1
                settings.mouseposx1=QCursor.pos().x()
                #mouseposy5=mouseposy4
                settings.mouseposy4=settings.mouseposy3
                settings.mouseposy3=settings.mouseposy2
                settings.mouseposy2=settings.mouseposy1
                settings.mouseposy1=QCursor.pos().y()

            if settings.onfloor == 1:
                if settings.set_fall:
                    settings.onfloor=0
                settings.draging=1
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('mousedrag')
            

            event.accept()
            #print(self.pos().x(), self.pos().y())

    def mouseReleaseEvent(self, event):
        """
        松开鼠标操作
        :param event:
        :return:
        """
        if event.button()==Qt.LeftButton:

            self.is_follow_mouse = False
            #self.setCursor(QCursor(Qt.ArrowCursor))
            self.setCursor(self.cursor_default)

            #print(self.mouse_moving, settings.onfloor)
            if settings.onfloor == 1 and not self.mouse_moving:
                self.patpat()

            else:

                anim_area = QRect(self.pos() + QPoint(self.width()//2-self.label.width()//2, 
                                                      self.height()-self.label.height()), 
                                  QSize(self.label.width(), self.label.height()))
                intersected = self.current_screen.intersected(anim_area)
                area = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                if area > 0.5:
                    pass
                else:
                    for screen in settings.screens:
                        if screen.geometry() == self.current_screen:
                            continue
                        intersected = screen.geometry().intersected(anim_area)
                        area_tmp = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                        if area_tmp > 0.5:
                            self.switch_screen(screen)
                    

                if settings.set_fall:
                    settings.onfloor=0
                    settings.draging=0
                    settings.prefall=1

                    settings.dragspeedx=(settings.mouseposx1-settings.mouseposx3)/2*settings.fixdragspeedx
                    settings.dragspeedy=(settings.mouseposy1-settings.mouseposy3)/2*settings.fixdragspeedy
                    settings.mouseposx1=settings.mouseposx3=0
                    settings.mouseposy1=settings.mouseposy3=0

                    if settings.dragspeedx > 0:
                        settings.fall_right = True
                    else:
                        settings.fall_right = False

                else:
                    settings.draging=0
                    self._move_customized(0,0)
                    settings.current_img = self.pet_conf.default.images[0]
                    self.set_img()
                    self.workers['Animation'].resume()
            self.mouse_moving = False


    def _init_widget(self) -> None:
        """
        初始化窗体, 无边框半透明窗口
        :return:
        """
        if settings.on_top_hint:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 是否跟随鼠标
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()

    def ontop_update(self):
        if settings.on_top_hint:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            if platform == 'win32':
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.SubWindow | Qt.NoDropShadowWindowHint)
            else:
                # SubWindow not work in MacOS
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()


    def _init_ui(self):
        # The Character ----------------------------------------------------------------------------
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.label.installEventFilter(self)
        #self.label.setStyleSheet("border : 2px solid blue")

        # system animations
        self.sys_src = _load_all_pic('sys')
        self.sys_conf = PetConfig.init_sys(self.sys_src) 
        # ------------------------------------------------------------------------------------------

        # Hover Timer --------------------------------------------------------
        self.status_frame = QFrame()
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)

        # 番茄时钟
        h_box3 = QHBoxLayout()
        h_box3.setContentsMargins(0,0,0,0)
        h_box3.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.tomatoicon = QLabel(self)
        self.tomatoicon.setFixedSize(statbar_h,statbar_h)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Tomato_icon.png'))
        self.tomatoicon.setScaledContents(True)
        self.tomatoicon.setPixmap(image)
        self.tomatoicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box3.addWidget(self.tomatoicon)
        self.tomato_time = RoundBarBase(fill_color="#ef4e50", parent=self) #QProgressBar(self, minimum=0, maximum=25, objectName='PetTM')
        self.tomato_time.setFormat('')
        self.tomato_time.setValue(25)
        self.tomato_time.setAlignment(Qt.AlignCenter)
        self.tomato_time.hide()
        self.tomatoicon.hide()
        h_box3.addWidget(self.tomato_time)

        # 专注时间
        h_box4 = QHBoxLayout()
        h_box4.setContentsMargins(0,status_margin,0,0)
        h_box4.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.focusicon = QLabel(self)
        self.focusicon.setFixedSize(statbar_h,statbar_h)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Timer_icon.png'))
        self.focusicon.setScaledContents(True)
        self.focusicon.setPixmap(image)
        self.focusicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box4.addWidget(self.focusicon)
        self.focus_time = RoundBarBase(fill_color="#47c0d2", parent=self) #QProgressBar(self, minimum=0, maximum=0, objectName='PetFC')
        self.focus_time.setFormat('')
        self.focus_time.setValue(0)
        self.focus_time.setAlignment(Qt.AlignCenter)
        self.focus_time.hide()
        self.focusicon.hide()
        h_box4.addWidget(self.focus_time)

        vbox.addStretch()
        vbox.addLayout(h_box3)
        vbox.addLayout(h_box4)

        self.status_frame.setLayout(vbox)
        #self.status_frame.setStyleSheet("border : 2px solid blue")
        self.status_frame.setContentsMargins(0,0,0,0)
        #self.status_box.addWidget(self.status_frame)
        #self.status_frame.hide()
        # ------------------------------------------------------------

        #Layout_1 ----------------------------------------------------
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)

        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.status_frame)

        image_hbox = QHBoxLayout()
        image_hbox.setContentsMargins(0,0,0,0)
        image_hbox.addStretch()
        image_hbox.addWidget(self.label, Qt.AlignBottom | Qt.AlignHCenter)
        image_hbox.addStretch()

        self.petlayout.addLayout(image_hbox, Qt.AlignBottom | Qt.AlignHCenter)
        self.petlayout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.petlayout.setContentsMargins(0,0,0,0)
        self.layout.addLayout(self.petlayout, Qt.AlignBottom | Qt.AlignHCenter)
        # ------------------------------------------------------------

        self.setLayout(self.layout)
        # ------------------------------------------------------------


        # 初始化背包
        #self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        settings.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        #self._init_Inventory()
        #self.showing_comp = 0

        # 客制化光标
        self.cursor_user = self.cursor()
        system_cursor_size = 32
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_default.png')):
            self.cursor_default = QCursor(QPixmap("res/icons/cursor_default.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_default = self.cursor_user
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_clicked.png')):
            self.cursor_clicked = QCursor(QPixmap("res/icons/cursor_clicked.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_clicked = self.cursor_user
        if os.path.exists(os.path.join(basedir, 'res/icons/cursor_dragged.png')):
            self.cursor_dragged = QCursor(QPixmap("res/icons/cursor_dragged.png").scaled(system_cursor_size, system_cursor_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.cursor_dragged = self.cursor_user

    '''
    def _init_Inventory(self):
        self.items_data = ItemData(HUNGERSTR=settings.HUNGERSTR, FAVORSTR=settings.FAVORSTR)
        self.inventory_window = Inventory(self.items_data)
        self.inventory_window.close_inventory.connect(self.show_inventory)
        self.inventory_window.use_item_inven.connect(self.use_item)
        self.inventory_window.item_note.connect(self.register_notification)
        self.inventory_window.item_anim.connect(self.item_drop_anim)
        self.addItem_toInven.connect(self.inventory_window.add_items)
        self.acc_withdrawed.connect(self.inventory_window.acc_withdrawed)
        self.fvlvl_changed_main_inve.connect(self.inventory_window.fvchange)
    '''


    def _set_menu(self, pets=()):
        """
        Option Menu
        """
        #menu = RoundMenu(self.tr("More Options"), self)
        #menu.setIcon(FIF.MENU)

        # Select action
        self.act_menu = RoundMenu(self.tr("Select Action"))
        self.act_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/jump.svg')))

        if platform == 'win32':
            self.start_follow_mouse = Action(QIcon(os.path.join(basedir,'res/icons/cursor.svg')),
                                            self.tr('Follow Cursor'),
                                            triggered = self.follow_mouse_act)
            self.act_menu.addAction(self.start_follow_mouse)
            self.act_menu.addSeparator()

        acts_config = settings.act_data.allAct_params[settings.petname]
        self.select_acts = [ _build_act(k, self.act_menu, self._show_act) for k,v in acts_config.items() if v['unlocked']]
        if self.select_acts:
            self.act_menu.addActions(self.select_acts)

        #menu.addMenu(self.act_menu)


        # Launch pet/partner
        self.companion_menu = RoundMenu(self.tr("Call Partner"))
        self.companion_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/partner.svg')))

        add_acts = [_build_act(name, self.companion_menu, self._add_pet) for name in pets]
        self.companion_menu.addActions(add_acts)

        #menu.addMenu(self.companion_menu)
        #menu.addSeparator()

        # Change Character
        self.change_menu = RoundMenu(self.tr("Change Character"))
        self.change_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/system/character.svg')))
        change_acts = [_build_act(name, self.change_menu, self._change_pet) for name in pets]
        self.change_menu.addActions(change_acts)
        #menu.addMenu(self.change_menu)

        # Drop on/off
        '''
        if settings.set_fall == 1:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/on.svg')),
                                      self.tr('Allow Drop'), menu)
        else:
            self.switch_fall = Action(QIcon(os.path.join(basedir,'res/icons/off.svg')),
                                      self.tr("Don't Drop"), menu)
        self.switch_fall.triggered.connect(self.fall_onoff)
        '''
        #menu.addAction(self.switch_fall)

        
        # Visit website - feature deprecated
        '''
        web_file = os.path.join(basedir, 'res/role/sys/webs.json')
        if os.path.isfile(web_file):
            web_dict = json.load(open(web_file, 'r', encoding='UTF-8'))

            self.web_menu = RoundMenu(self.tr("Website"), menu)
            self.web_menu.setIcon(QIcon(os.path.join(basedir,'res/icons/website.svg')))

            web_acts = [_build_act_param(name, web_dict[name], self.web_menu, self.open_web) for name in web_dict]
            self.web_menu.addActions(web_acts)
            menu.addMenu(self.web_menu)
        '''
            
        #menu.addSeparator()
        #self.menu = menu
        #self.menu.addAction(Action(FIF.POWER_BUTTON, self.tr('Exit'), triggered=self.quit))


    def _update_fvlock(self):

        # Update selectable animations
        acts_config = settings.act_data.allAct_params[settings.petname]
        for act_name, act_conf in acts_config.items():
            if act_conf['unlocked']:
                if act_name not in [acti.text() for acti in self.select_acts]:
                    new_act = _build_act(act_name, self.act_menu, self._show_act)
                    self.act_menu.addAction(new_act)
                    self.select_acts.append(new_act)
            else:
                if act_name in [acti.text() for acti in self.select_acts]:
                    act_index = [acti.text() for acti in self.select_acts].index(act_name)
                    self.act_menu.removeAction(self.select_acts[act_index])
                    self.select_acts.remove(self.select_acts[act_index])


    def _set_Statusmenu(self):

        # Character Name
        self.statusTitle = QWidget()
        hboxTitle = QHBoxLayout(self.statusTitle)
        hboxTitle.setContentsMargins(0,0,0,0)
        self.nameLabel = CaptionLabel(self.curr_pet_name, self)
        setFont(self.nameLabel, 14, QFont.DemiBold)
        #self.nameLabel.setFixedWidth(75)

        self.daysLabel = CaptionLabel(" EchoPet Demo", self)
        setFont(self.daysLabel, 14, QFont.Normal)

        hboxTitle.addStretch(1)
        hboxTitle.addWidget(self.nameLabel, Qt.AlignLeft | Qt.AlignVCenter)
        hboxTitle.addStretch(1)
        hboxTitle.addWidget(self.daysLabel, Qt.AlignRight | Qt.AlignVCenter)
        #hboxTitle.addStretch(1)
        self.statusTitle.setFixedSize(225, 25)

        # # Status Title
        # hp_tier = settings.pet_data.hp_tier
        # statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
        # self.statLabel = CaptionLabel(statusText, self)
        # setFont(self.statLabel, 14, QFont.Normal)

        # Level Badge
        lvlWidget = QWidget()
        h_box0 = QHBoxLayout(lvlWidget)
        h_box0.setContentsMargins(0,0,0,0)
        h_box0.setSpacing(5)
        h_box0.setAlignment(Qt.AlignCenter)
        lvlLable = CaptionLabel(self.tr("Level"))
        setFont(lvlLable, 13, QFont.Normal)
        lvlLable.adjustSize()
        lvlLable.setFixedSize(43, lvlLable.height())
        self.lvl_badge = LevelBadge(settings.pet_data.fv_lvl)
        h_box0.addWidget(lvlLable)
        #h_box0.addStretch(1)
        h_box0.addWidget(self.lvl_badge)
        h_box0.addStretch(1)
        lvlWidget.setFixedSize(250, 25)

        # Hunger status
        hpWidget = QWidget()
        h_box1 = QHBoxLayout(hpWidget)
        h_box1.setContentsMargins(0,0,0,0) #status_margin,0,0)
        h_box1.setSpacing(5)
        h_box1.setAlignment(Qt.AlignCenter) #AlignBottom | Qt.AlignHCenter)
        hpLable = CaptionLabel(self.tr("Satiety"))
        setFont(hpLable, 13, QFont.Normal)
        hpLable.adjustSize()
        hpLable.setFixedSize(43, hpLable.height())
        self.hpicon = QLabel(self)
        self.hpicon.setFixedSize(icons_wh,icons_wh)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/HP_icon.png'))
        self.hpicon.setScaledContents(True)
        self.hpicon.setPixmap(image)
        self.hpicon.setAlignment(Qt.AlignCenter) #AlignBottom | Qt.AlignRight)
        h_box1.addWidget(hpLable)
        h_box1.addStretch(1)
        h_box1.addWidget(self.hpicon)
        #h_box1.addStretch(1)
        self.pet_hp = DP_HpBar(self, minimum=0, maximum=100, objectName='PetHP')
        self.pet_hp.hp_updated.connect(self._hp_updated)
        h_box1.addWidget(self.pet_hp)
        h_box1.addStretch(1)

        # favor status
        fvWidget = QWidget()
        h_box2 = QHBoxLayout(fvWidget)
        h_box2.setContentsMargins(0,0,0,0) #status_margin,0,0)
        h_box2.setSpacing(5)
        h_box2.setAlignment(Qt.AlignCenter) #Qt.AlignBottom | Qt.AlignHCenter)
        fvLable = CaptionLabel(self.tr("Favor"))
        setFont(fvLable, 13, QFont.Normal)
        fvLable.adjustSize()
        fvLable.setFixedSize(43, fvLable.height())
        self.emicon = QLabel(self)
        self.emicon.setFixedSize(icons_wh,icons_wh)
        image = QPixmap()
        image.load(os.path.join(basedir, 'res/icons/Fv_icon.png'))
        self.emicon.setScaledContents(True)
        self.emicon.setPixmap(image)
        #self.emicon.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        h_box2.addWidget(fvLable, Qt.AlignHCenter | Qt.AlignTop)
        h_box2.addStretch(1)
        h_box2.addWidget(self.emicon)
        self.pet_fv = DP_FvBar(self, minimum=0, maximum=100, objectName='PetEM')
        self.pet_fv.fv_updated.connect(self._fv_updated)

        self.pet_hp.hptier_changed.connect(self.hpchange)
        self.pet_fv.fvlvl_changed.connect(self.fvchange)
        h_box2.addWidget(self.pet_fv)
        h_box2.addStretch(1)

        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)
        self.pet_hp.setFixedSize(145, 15)
        self.pet_fv.setFixedSize(145, 15)

        # Status Widget
        self.statusWidget = QWidget()
        self.statusWidget.setObjectName("StatusWidget")
        StatVbox = QVBoxLayout(self.statusWidget)
        StatVbox.setContentsMargins(10, 10, 10, 10)
        StatVbox.setSpacing(5)
        
        # LCD Screen style
        self.lcd_container = QFrame()
        self.lcd_container.setObjectName("LcdScreen")
        lcd_layout = QVBoxLayout(self.lcd_container)
        lcd_layout.setContentsMargins(8, 8, 8, 8)
        
        # Avatar and Status
        top_row = QHBoxLayout()
        self.menu_avatar = QLabel()
        self.menu_avatar.setFixedSize(50, 50)
        self.menu_avatar.setAlignment(Qt.AlignCenter)
        
        img_path = Path(__file__).resolve().parents[2] / "1.png"
        if img_path.exists():
            self.menu_avatar.setPixmap(QPixmap(str(img_path)).scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            self.menu_avatar.setText("Avatar")
            
        status_layout = QVBoxLayout()
        status_label_title = QLabel("STATUS:")
        status_label_title.setObjectName("LcdSmall")
        self.pet_status_value = QLabel("FINDING VIBE...")
        self.pet_status_value.setObjectName("LcdSmall")
        self.pet_status_value.setWordWrap(True)
        
        eq_label = QLabel("▂▃▅▇█▆▅▃▂")
        eq_label.setObjectName("LcdSmall")
        
        status_layout.addWidget(status_label_title)
        status_layout.addWidget(self.pet_status_value)
        status_layout.addWidget(eq_label)
        status_layout.addStretch()
        
        top_row.addWidget(self.menu_avatar)
        top_row.addLayout(status_layout, stretch=1)
        lcd_layout.addLayout(top_row)
        
        # Track Info (Paper label style)
        self.track_container = QFrame()
        self.track_container.setObjectName("TrackLabel")
        track_layout = QVBoxLayout(self.track_container)
        track_layout.setContentsMargins(5, 5, 5, 5)
        self.recommendation_value = QLabel("▶ NO TRACK")
        self.recommendation_value.setObjectName("TypewriterText")
        self.recommendation_value.setWordWrap(True)
        track_layout.addWidget(self.recommendation_value)
        
        # Player Status
        self.player_status_value = QLabel("STOPPED")
        self.player_status_value.setObjectName("LcdSmall")
        
        StatVbox.addWidget(self.lcd_container)
        StatVbox.addWidget(self.track_container)
        StatVbox.addWidget(self.player_status_value, alignment=Qt.AlignRight)
        
        self.statusWidget.setFixedSize(260, 160)
        
        self.statusWidget.setStyleSheet("""
            QWidget#StatusWidget {
                background-color: #E8E6DF;
                border-radius: 8px;
                border: 2px solid #D0CDBE;
            }
            QFrame#LcdScreen {
                background-color: #9EAB88;
                border: 3px solid #4A4F40;
                border-radius: 4px;
            }
            QLabel#LcdSmall {
                color: #2A3020;
                font-family: "Courier New", Courier, monospace;
                font-size: 10px;
                font-weight: bold;
            }
            QFrame#TrackLabel {
                background-color: #D2B48C; /* Vintage paper color */
                border: 1px solid #A0522D;
                border-radius: 2px;
                margin-top: 5px;
            }
            QLabel#TypewriterText {
                color: #1A1A18;
                font-family: "Courier New", Courier, monospace;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        self.StatMenu = RoundMenu(parent=self)
        # Apply global style to RoundMenu to match the casing
        self.StatMenu.setStyleSheet("""
            RoundMenu {
                background-color: #E8E6DF;
                border: 2px solid #D0CDBE;
                border-radius: 8px;
            }
            Action {
                font-family: "Courier New", Courier, monospace;
                font-weight: bold;
                color: #4A4843;
                background-color: #DCD9D0;
                border: 2px solid #B5B2A5;
                border-radius: 4px;
                padding: 10px;
                margin: 4px 10px;
            }
            Action:hover {
                background-color: #C4C1B3;
                border: 2px solid #A3A093;
            }
        """)
        
        self.StatMenu.addWidget(self.statusWidget, selectable=False)
        self.StatMenu.addSeparator()

        self.demo_menu = RoundMenu(self.tr("Demo States"))
        self.demo_menu.setIcon(QIcon(os.path.join(basedir, 'res/icons/focus.svg')))
        demo_states = [
            ("Idle", "idle"),
            ("Focus", "focus"),
            ("Tired", "tired"),
            ("Frustrated", "frustrated"),
            ("Sad", "sad"),
        ]
        for label, state_name in demo_states:
            self.demo_menu.addAction(
                Action(
                    QIcon(os.path.join(basedir, 'res/icons/Dialogue_icon.png')),
                    self.tr(label),
                    triggered=lambda _checked=False, s=state_name: self.apply_mock_state(s),
                )
            )

        self.debug_menu = RoundMenu(self.tr("[ DEBUG ]"))
        self.debug_menu.setIcon(QIcon(os.path.join(basedir, 'res/icons/system/more.svg')))
        self.debug_menu.addActions([
            Action(QIcon(os.path.join(basedir,'res/icons/dashboard.svg')), self.tr('Dashboard'), triggered=self._show_dashboard),
            Action(QIcon(os.path.join(basedir,'res/icons/SystemPanel.png')), self.tr('System'), triggered=self._show_controlPanel),
        ])
        self.debug_menu.addSeparator()
        self.debug_menu.addMenu(self.demo_menu)
        if self.act_menu.actions():
            self.debug_menu.addMenu(self.act_menu)
        if self.companion_menu.actions():
            self.debug_menu.addMenu(self.companion_menu)
        if self.change_menu.actions():
            self.debug_menu.addMenu(self.change_menu)

        self.StatMenu.addActions([
            Action(QIcon(os.path.join(basedir,'res/icons/Dialogue_icon.png')), self.tr('[ OPEN ECHOPET ]'), triggered=self.open_input_panel),
        ])
        self.StatMenu.addMenu(self.debug_menu)
        self.StatMenu.addSeparator()
        
        self.StatMenu.addActions([
            Action(FIF.POWER_BUTTON, self.tr('[ EJECT / EXIT ]'), triggered=self.quit),
        ])
        self._refresh_echopet_status_summary()


    # def _update_statusTitle(self, hp_tier):
    #     statusText = self.tr("Status: ") + f"{settings.TIER_NAMES[hp_tier]}"
    #     self.statLabel.setText(statusText)


    def _show_Staus_menu(self):
        """
        展示右键菜单
        :return:
        """
        # 光标位置弹出菜单
        self.StatMenu.popup(QCursor.pos()-QPoint(0, self.StatMenu.height()-20))

    def _friendly_pet_state_label(self, state_name):
        mapping = {
            "idle": "待命中",
            "focus": "专注陪伴中",
            "tired": "疲惫安抚中",
            "frustrated": "正在帮你缓一缓",
            "sad": "正在安静陪伴",
        }
        return mapping.get(state_name, "待命中")

    def _friendly_player_status_label(self, status_name):
        mapping = {
            "idle": "未播放",
            "loading": "正在准备歌曲",
            "playing": "正在播放",
            "paused": "已暂停",
            "error": "播放异常",
        }
        return mapping.get(status_name, status_name or "未播放")

    def _refresh_echopet_status_summary(self):
        if not hasattr(self, "pet_status_value"):
            return
        recommendation = self.current_track or {}
        title = recommendation.get("title", "")
        artist = recommendation.get("artist", "")
        if title and artist:
            recommendation_text = f"{title} - {artist}"
        else:
            recommendation_text = title or "暂无"
        self.pet_status_value.setText(self.current_pet_status_text or self._friendly_pet_state_label(self.current_agent_state))
        self.recommendation_value.setText(recommendation_text)
        self.player_status_value.setText(self._friendly_player_status_label(self.current_player_status))

    def _add_pet(self, pet_name: str):
        pet_acc = {'name':'pet', 'pet_name':pet_name}
        #self.setup_acc.emit(pet_acc, int(self.current_screen.topLeft().x() + random.uniform(0.4,0.7)*self.screen_width), self.pos().y())
        # To accomodate any subpet that always follows main, change the position to top middle pos of pet
        self.setup_acc.emit(pet_acc, int( self.pos().x() + self.width()/2 ), self.pos().y())

    def open_web(self, web_address):
        try:
            webbrowser.open(web_address)
        except:
            return
    '''
    def freeze_pet(self):
        """stop all thread, function for save import"""
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread('Scheduler')
        #del self.threads, self.workers
    '''
    
    def refresh_pet(self):
        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')

        # Change status
        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)

        # Change status related behavior
        #self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        #self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)

        # Animation config data update
        settings.act_data._pet_refreshed(settings.pet_data.fv_lvl)
        self.refresh_acts.emit()

        # cancel default animation if any
        '''
        defaul_act = settings.defaultAct[self.curr_pet_name]
        if defaul_act is not None:
            self._set_defaultAct(self, defaul_act)
        self._update_fvlock()
        # add default animation back
        if defaul_act in [acti.text() for acti in self.defaultAct_menu.actions()]:
            self._set_defaultAct(self, defaul_act)
        '''

        # Update BackPack
        #self._init_Inventory()
        self.refresh_bag.emit()
        self._set_menu(self.pets)
        self._set_Statusmenu()
        self._set_tray()

        # restart animation and interaction
        self.runAnimation()
        self.runInteraction()
        
        # restore data system
        settings.pet_data.frozen_data = False

        # Compensate items if any
        self._setup_compensate()
    

    def _change_pet(self, pet_name: str) -> None:
        """
        改变宠物
        :param pet_name: 宠物名称
        :return:
        """
        if self.curr_pet_name == pet_name:
            return
        
        # close all accessory widgets (subpet, accessory animation, etc.)
        self.close_all_accs.emit()

        # stop animation thread and start again
        self.stop_thread('Animation')
        self.stop_thread('Interaction')

        # reload pet data
        settings.pet_data._change_pet(pet_name)

        # reload new pet
        self.init_conf(pet_name)

        # Change status
        self.pet_hp.init_HP(settings.pet_data.hp, sys_hp_interval) #2)
        self.pet_fv.init_FV(settings.pet_data.fv, settings.pet_data.fv_lvl)

        # Change status related behavior
        #self.workers['Animation'].hpchange(settings.pet_data.hp_tier, None)
        #self.workers['Animation'].fvchange(settings.pet_data.fv_lvl)

        # Update Backpack
        #self._init_Inventory()
        self.refresh_bag.emit()
        self.refresh_acts.emit()

        self.change_note.emit()
        self.repaint()
        self._setup_ui()

        self.runAnimation()
        self.runInteraction()

        self.workers['Scheduler'].send_greeting()
        # Compensate items if any
        self._setup_compensate()
        # Due to Qt internal behavior, sometimes has to manually correct the position back
        pos_x, pos_y = self.pos().x(), self.pos().y()
        QTimer.singleShot(10, lambda: self.move(pos_x, pos_y))

    def init_conf(self, pet_name: str) -> None:
        """
        初始化宠物窗口配置
        :param pet_name: 宠物名称
        :return:
        """
        self.curr_pet_name = pet_name
        settings.petname = pet_name
        settings.tunable_scale = settings.scale_dict.get(pet_name, 1.0)
        pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, pic_dict) #settings.size_factor)
        
        self.margin_value = 0 #0.1 * max(self.pet_conf.width, self.pet_conf.height) # 用于将widgets调整到合适的大小
        # Add customized animation
        settings.act_data.init_actData(pet_name, settings.pet_data.hp_tier, settings.pet_data.fv_lvl)
        self._load_custom_anim()
        settings.pet_conf = self.pet_conf

        # Update coin name and image according to the pet config
        if self.pet_conf.coin_config:
            coin_config = self.pet_conf.coin_config.copy()
            if not coin_config['image']:
                coin_config['image'] = settings.items_data.default_coin['image']
            settings.items_data.coin = coin_config
        else:
            settings.items_data.coin = settings.items_data.default_coin.copy()

        # Init bubble behavior manager
        self.bubble_manager = BubbleManager()
        self.bubble_manager.register_bubble.connect(self.register_bubbleText)

        self._set_menu(self.pets)
        self._set_Statusmenu()
        self._set_tray()


    def _load_custom_anim(self):
        acts_conf = settings.act_data.allAct_params[settings.petname]
        for act_name, act_conf in acts_conf.items():
            if act_conf['act_type'] == 'customized' and act_name not in self.pet_conf.custom_act:
                # generate new Act objects for cutomized animation
                acts = []
                for act in act_conf.get('act_list', []):
                    acts.append(self._prepare_act_obj(act))
                accs = []
                for act in act_conf.get('acc_list', []):
                    accs.append(self._prepare_act_obj(act))
                # save the new animation config with same format as self.pet_conf.accessory_act
                self.pet_conf.custom_act[act_name] = {"act_list": acts,
                                                      "acc_list": accs,
                                                      "anchor": act_conf.get('anchor_list',[]),
                                                      "act_type": act_conf['status_type']}

    def _prepare_act_obj(self, actobj):
        
        # if this act is a skipping act e.g. [60, 20]
        if len(actobj) == 2:
            return actobj
        else:
            act_conf_name = actobj[0]
            act_idx_start = actobj[1]
            act_idx_end = actobj[2]+1
            act_repeat_num = actobj[3]
            new_actobj = self.pet_conf.act_dict[act_conf_name].customized_copy(act_idx_start, act_idx_end, act_repeat_num)
            return new_actobj

    def updateList(self):
        self.workers['Animation'].update_prob()

    def _addNewAct(self, act_name):
        acts_config = settings.act_data.allAct_params[settings.petname]
        act_conf = acts_config[act_name]

        # Add to pet_conf
        acts = []
        for act in act_conf.get('act_list', []):
            acts.append(self._prepare_act_obj(act))
        accs = []
        for act in act_conf.get('acc_list', []):
            accs.append(self._prepare_act_obj(act))
        self.pet_conf.custom_act[act_name] = {"act_list": acts,
                                                "acc_list": accs,
                                                "anchor": act_conf.get('anchor_list',[]),
                                                "act_type": act_conf['status_type']}
        # update random action prob
        self.updateList()
        # Add to menu
        if act_conf['unlocked']:
            select_act = _build_act(act_name, self.act_menu, self._show_act)
            self.select_acts.append(select_act)
            self.act_menu.addAction(select_act)
    
    def _deleteAct(self, act_name):
        # delete from self.pet_config
        self.pet_conf.custom_act.pop(act_name)
        # update random action prob
        self.updateList()

        # delete from menu
        act_index = [acti.text() for acti in self.select_acts].index(act_name)
        self.act_menu.removeAction(self.select_acts[act_index])
        self.select_acts.remove(self.select_acts[act_index])


    def _setup_ui(self):

        #bar_width = int(max(100*settings.size_factor, 0.5*self.pet_conf.width))
        bar_width = int(max(100, 0.5*self.pet_conf.width))
        bar_width = int(min(200, bar_width))
        self.tomato_time.setFixedSize(bar_width, statbar_h-5)
        self.focus_time.setFixedSize(bar_width, statbar_h-5)

        self.reset_size(setImg=False)

        settings.previous_img = settings.current_img
        settings.current_img = self.pet_conf.default.images[0] #list(pic_dict.values())[0]
        settings.previous_anchor = [0, 0] #settings.current_anchor
        settings.current_anchor = [int(i*settings.tunable_scale) for i in self.pet_conf.default.anchor]
        self.set_img()
        self.border = self.pet_conf.width/2

        
        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.current_screen.topLeft().x() + int(screen_width*0.8) - self.width()//2
        y = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)
        if settings.previous_anchor != settings.current_anchor:
            self.move(self.pos().x() - settings.previous_anchor[0] + settings.current_anchor[0],
                      self.pos().y() - settings.previous_anchor[1] + settings.current_anchor[1])
            #self.move(self.pos().x()-settings.previous_anchor[0]*settings.tunable_scale+settings.current_anchor[0]*settings.tunable_scale,
            #          self.pos().y()-settings.previous_anchor[1]*settings.tunable_scale+settings.current_anchor[1]*settings.tunable_scale)

    def _init_echopet_frontend(self):
        self.agent_client = AgentClient()
        self.whisper_adapter = WhisperAdapter(self.agent_client)
        self.audio_recorder = AudioRecorder(self)
        self.input_panel = InputPanel()
        self.input_panel.submit_requested.connect(self.submit_user_text)
        self.input_panel.mock_state_requested.connect(self.apply_mock_state)
        self.input_panel.player_event_requested.connect(self.send_player_event)
        self.input_panel.record_requested.connect(self.toggle_recording)
        self.agent_result_ready.connect(self._handle_agent_result_ready)
        self.player_event_result_ready.connect(self._handle_player_event_result_ready)
        self.transcript_ready.connect(self._handle_transcript_ready)
        self.transcript_failed.connect(self._handle_transcript_failed)

        self.audio_recorder.recording_started.connect(self._handle_recording_started)
        self.audio_recorder.recording_finished.connect(self._handle_recording_finished)
        self.audio_recorder.recording_failed.connect(self._handle_recording_failed)

        self.player_status_poller = PlayerStatusPoller(self.agent_client, parent=self)
        self.player_status_poller.status_updated.connect(self.update_player_status)

        self.move_sig.connect(lambda _x, _y: self._sync_input_panel_position())

    def _sync_input_panel_position(self):
        if not self.input_panel or not self.input_panel.isVisible():
            return
        offset_x = self.width() + 20
        offset_y = max(-40, -self.input_panel.height() + self.height())
        self.input_panel.move(self.pos().x() - offset_x, self.pos().y() + offset_y)

    def open_input_panel(self):
        if not self.input_panel:
            return
        self._sync_input_panel_position()
        self.input_panel.show()
        self.input_panel.raise_()
        self.input_panel.activateWindow()

    def toggle_recording(self):
        if not self.audio_recorder:
            return
        self.audio_recorder.toggle()

    def submit_user_text(self, text, input_source="text"):
        clean_text = text.strip()
        if not clean_text:
            self.register_bubbleText({"message": self.tr("Please enter a message first."), "icon": None})
            return

        self.last_user_text = clean_text
        self.current_pet_status_text = "正在帮你找歌"
        self.current_player_status = "loading"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_busy(True, "提示: 正在分析中...")
        threading.Thread(
            target=self._submit_user_text_async,
            args=(clean_text, input_source),
            daemon=True,
        ).start()

    def apply_mock_state(self, state_name):
        text = self.last_user_text or state_name
        result = self.agent_client.build_mock_result(text=text, forced_state=state_name)
        result["_mode"] = "mock"
        self.apply_agent_result(result)
        self.open_input_panel()

    def _submit_user_text_async(self, text, input_source):
        result = self.agent_client.submit_text(text, input_source=input_source)
        self.agent_result_ready.emit(result)

    def _handle_agent_result_ready(self, result):
        self.apply_agent_result(result)
        if self.input_panel:
            self.input_panel.set_busy(False)

    def _handle_recording_started(self):
        self.current_pet_status_text = "正在听你说话"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_recording(True)

    def _handle_recording_finished(self, audio_bytes, audio_format):
        self.current_pet_status_text = "正在转写语音"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_recording(False)
            self.input_panel.set_busy(True, "提示: 正在转写录音...")
        threading.Thread(
            target=self._transcribe_audio_async,
            args=(audio_bytes, audio_format),
            daemon=True,
        ).start()

    def _handle_recording_failed(self, message):
        self.current_pet_status_text = "录音失败"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_recording(False)
            self.input_panel.set_busy(False, f"提示: {message}")

    def _transcribe_audio_async(self, audio_bytes, audio_format):
        try:
            result = self.whisper_adapter.transcribe_audio_bytes(audio_bytes, audio_format=audio_format)
            transcript = result.get("transcript", "").strip()
            if not transcript:
                raise RuntimeError("转写结果为空")
            self.transcript_ready.emit(transcript)
        except Exception as exc:
            self.transcript_failed.emit(str(exc))

    def _handle_transcript_ready(self, transcript):
        self.current_pet_status_text = "文字已准备好"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_busy(False)
            self.input_panel.set_transcript(transcript)
            self.input_panel.show_status("提示: 录音已转写，请确认文本后再提交")
        self.register_bubbleText(
            {
                "bubble_type": "agent_transcript",
                "message": self.tr("录音已转成文字，确认后再发给我吧。"),
                "icon": None,
                "timeout": 4,
            }
        )

    def _handle_transcript_failed(self, message):
        self.current_pet_status_text = "转写失败"
        self.current_player_status = "idle"
        self._refresh_echopet_status_summary()
        if self.input_panel:
            self.input_panel.set_busy(False, f"提示: {message}")
            self.input_panel.set_recording(False)
        self.register_bubbleText(
            {
                "bubble_type": "agent_transcript_error",
                "message": f"转写失败: {message}",
                "icon": None,
                "timeout": 4,
            }
        )

    def apply_agent_result(self, result):
        mapped_result = map_agent_result(result)
        self.current_agent_state = mapped_result["pet_state"]
        self.current_track = mapped_result.get("recommendation") or {}
        self.current_player_status = mapped_result.get("player_status", {}).get("status", "idle")
        if self.current_player_status == "loading":
            self.current_pet_status_text = "正在帮你准备歌曲"
        else:
            self.current_pet_status_text = self._friendly_pet_state_label(self.current_agent_state)
        self._refresh_echopet_status_summary()

        self.apply_pet_state(mapped_result["pet_state"])
        self.register_bubbleText(
            {
                "bubble_type": "agent_result",
                "message": mapped_result["bubble_text"],
                "icon": None,
                "timeout": 6,
            }
        )

        if self.input_panel:
            self.input_panel.show_agent_result(mapped_result)

        recommendation = mapped_result.get("recommendation") or {}
        if recommendation.get("title"):
            message = self.tr("Ready: ") + recommendation.get("title", "")
            self.register_notification("system", message)
        if mapped_result.get("debug_mode") == "api":
            self.start_player_status_polling()

    def apply_pet_state(self, state_name):
        acts_config = settings.act_data.allAct_params.get(settings.petname, {})
        action_name = pick_action_for_state(state_name, acts_config.keys())
        if action_name:
            self._show_act(action_name)

    def start_player_status_polling(self):
        if self.player_status_poller and not self.player_status_poller.timer.isActive():
            self.player_status_poller.start()

    def update_player_status(self, status_payload):
        if not status_payload:
            return
        self.current_track = {
            "id": status_payload.get("track_id", ""),
            "title": status_payload.get("title", ""),
            "artist": status_payload.get("artist", ""),
        }
        self.current_player_status = status_payload.get("status", "idle")
        if self.current_player_status == "playing":
            self.current_pet_status_text = "正在陪你听歌"
        elif self.current_player_status == "loading":
            self.current_pet_status_text = "正在帮你准备歌曲"
        elif self.current_player_status == "paused":
            self.current_pet_status_text = "歌曲暂停中"
        elif self.current_player_status == "error":
            self.current_pet_status_text = "播放出了点问题"
        elif self.current_player_status == "idle":
            self.current_pet_status_text = self._friendly_pet_state_label(self.current_agent_state)
        self._refresh_echopet_status_summary()

        if self.input_panel and self.input_panel.isVisible():
            title = status_payload.get("title", "")
            status = status_payload.get("status", "idle")
            if status == "idle" and not title:
                if self.player_status_poller:
                    self.player_status_poller.stop()
                return
            if title:
                self.input_panel.show_status(f"提示: 播放器状态 {status} / {title}")
            else:
                self.input_panel.show_status(f"提示: 播放器状态 {status}")
        if status_payload.get("status") in ("idle", "error") and self.player_status_poller:
            self.player_status_poller.stop()

    def send_player_event(self, session_id, completion_rate, ended_reason):
        threading.Thread(
            target=self._send_player_event_async,
            args=(session_id, completion_rate, ended_reason),
            daemon=True,
        ).start()

    def _send_player_event_async(self, session_id, completion_rate, ended_reason):
        response = self.agent_client.send_player_event(session_id, completion_rate, ended_reason)
        message = response.get("message", "播放事件已上报")
        self.player_event_result_ready.emit(message)

    def _handle_player_event_result_ready(self, message):
        if self.input_panel:
            self.input_panel.show_status(f"提示: {message}")
        self.register_bubbleText(
            {
                "bubble_type": "agent_player_event",
                "message": message,
                "icon": None,
                "timeout": 4,
            }
        )

    '''
    def eventFilter(self, object, event):
        return
    
        if event.type() == QEvent.Enter:
            self.status_frame.show()
            return True
        elif event.type() == QEvent.Leave:
            self.status_frame.hide()
        return False
    '''

    def _set_tray(self) -> None:
        """
        设置最小化托盘
        :return:
        """
        if self.tray is None:
            self.tray = SystemTray(self.StatMenu, self) #QSystemTrayIcon(self)
            self.tray.setIcon(QIcon(os.path.join(basedir, 'res/icons/icon.png')))
            self.tray.show()
        else:
            self.tray.setMenu(self.StatMenu)
            self.tray.show()

    def reset_size(self, setImg=True):
        #self.setFixedSize((max(self.pet_hp.width()+statbar_h,self.pet_conf.width)+self.margin_value)*max(1.0,settings.tunable_scale),
        #                  (self.margin_value+4*statbar_h+self.pet_conf.height)*max(1.0, settings.tunable_scale))
        self.setFixedSize( int(max(self.tomato_time.width()+statbar_h,self.pet_conf.width*settings.tunable_scale)),
                           int(2*statbar_h+self.pet_conf.height*settings.tunable_scale)
                         )

        #self.label.setFixedWidth(self.width())

        # 初始位置
        #screen_geo = QDesktopWidget().availableGeometry() #QDesktopWidget().screenGeometry()
        screen_width = self.screen_width #screen_geo.width()
        work_height = self.screen_height #screen_geo.height()
        x = self.pos().x() + settings.current_anchor[0]
        if settings.set_fall:
            y = self.current_screen.topLeft().y() + work_height-self.height()+settings.current_anchor[1]
        else:
            y = self.pos().y() + settings.current_anchor[1]
        # make sure that for all stand png, png bottom is the ground
        #self.floor_pos = work_height-self.height()
        self.floor_pos = self.current_screen.topLeft().y() + work_height - self.height()
        self.move(x,y)
        self.move_sig.emit(self.pos().x()+self.width()//2, self.pos().y()+self.height())

        if setImg:
            self.set_img()

    def set_img(self): #, img: QImage) -> None:
        """
        为窗体设置图片
        :param img: 图片
        :return:
        """
        #print(settings.previous_anchor, settings.current_anchor)
        if settings.previous_anchor != settings.current_anchor:
            self.move(self.pos().x()-settings.previous_anchor[0]+settings.current_anchor[0],
                      self.pos().y()-settings.previous_anchor[1]+settings.current_anchor[1])

        width_tmp = int(settings.current_img.width()*settings.tunable_scale)
        height_tmp = int(settings.current_img.height()*settings.tunable_scale)

        # HighDPI-compatible scaling solution
        # self.label.setScaledContents(True)
        self.label.setFixedSize(width_tmp, height_tmp)
        self.label.setPixmap(settings.current_img) #QPixmap.fromImage(settings.current_img))
        # previous scaling soluton
        #self.label.resize(width_tmp, height_tmp)
        #self.label.setPixmap(QPixmap.fromImage(settings.current_img.scaled(width_tmp, height_tmp,
        #                                                                 aspectMode=Qt.KeepAspectRatio,
        #                                                                 mode=Qt.SmoothTransformation)))
        self.image = settings.current_img

    def _compensate_rewards(self):
        self.compensate_rewards.emit()
        # Note user if App updates available
        if settings.UPDATE_NEEDED:
            self.register_notification("system",
                                       self.tr("App update available! Please check System - Settings - Check Updates for detail."))

    def register_notification(self, note_type, message):
        self.setup_notification.emit(note_type, message)


    def register_bubbleText(self, bubble_dict:dict):
        self.setup_bubbleText.emit(bubble_dict, self.pos().x()+self.width()//2, self.pos().y()+self.height())

    def _process_greeting_mssg(self, bubble_dict:dict):
        self.bubble_manager.add_usertag(bubble_dict, 'end', send=True)

    def register_accessory(self, accs):
        self.setup_acc.emit(accs, self.pos().x()+self.width()//2, self.pos().y()+self.height())


    def _change_status(self, status, change_value, from_mod='Scheduler', send_note=False):
        # Check system status
        if from_mod == 'Scheduler' and is_system_locked() and settings.auto_lock:
            print("System locked, skip HP and FV changes")
            return
        if status not in ['hp','fv']:
            return
        elif status == 'hp':
            
            diff = self.pet_hp.updateValue(change_value, from_mod)

        elif status == 'fv':
            
            diff = self.pet_fv.updateValue(change_value, from_mod)

        if send_note:

            if diff > 0:
                diff = '+%s'%diff
            elif diff < 0:
                diff = str(diff)
            else:
                return
            if status == 'hp':
                message = self.tr('Satiety') + " " f'{diff}'
            else:
                message = self.tr('Favorability') + " " f'{diff}' #'好感度 %s'%diff
            self.register_notification('status_%s'%status, message)
        
        # Periodically triggered events
        if status == 'hp' and from_mod == 'Scheduler': # avoid being called in both hp and fv
            # Random Bubble
            if random.uniform(0, 1) < settings.PP_BUBBLE:
                self.bubble_manager.trigger_scheduled()

            # Auto-Feed
            if settings.pet_data.hp <= settings.AUTOFEED_THRESHOLD*settings.HP_INTERVAL:
                self.autofeed.emit()

    def _hp_updated(self, hp):
        self.hp_updated.emit(hp)

    def _fv_updated(self, fv, fv_lvl):
        self.fv_updated.emit(fv, fv_lvl)


    def _change_time(self, status, timeleft):
        if status not in ['tomato','tomato_start','tomato_rest','tomato_end',
                          'focus_start','focus','focus_end','tomato_cencel','focus_cancel']:
            return

        if status in ['tomato','tomato_rest','tomato_end','focus','focus_end']:
            self.taskUI_Timer_update.emit()

        if status == 'tomato_start':
            self.tomato_time.setMaximum(25)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
            #self.tomato_window.newTomato()
        elif status == 'tomato_rest':
            self.tomato_time.setMaximum(5)
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
            self.single_pomo_done.emit()
        elif status == 'tomato':
            self.tomato_time.setValue(timeleft)
            self.tomato_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'tomato_end':
            self.tomato_time.setValue(0)
            self.tomato_time.setFormat('')
            #self.tomato_window.endTomato()
            self.taskUI_task_end.emit()
        elif status == 'tomato_cencel':
            self.tomato_time.setValue(0)
            self.tomato_time.setFormat('')

        elif status == 'focus_start':
            if timeleft == 0:
                self.focus_time.setMaximum(1)
                self.focus_time.setValue(0)
                self.focus_time.setFormat('%s min'%(int(timeleft)))
            else:
                self.focus_time.setMaximum(timeleft)
                self.focus_time.setValue(timeleft)
                self.focus_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'focus':
            self.focus_time.setValue(timeleft)
            self.focus_time.setFormat('%s min'%(int(timeleft)))
        elif status == 'focus_end':
            self.focus_time.setValue(0)
            self.focus_time.setMaximum(0)
            self.focus_time.setFormat('')
            #self.focus_window.endFocus()
            self.taskUI_task_end.emit()
        elif status == 'focus_cancel':
            self.focus_time.setValue(0)
            self.focus_time.setMaximum(0)
            self.focus_time.setFormat('')

    def use_item(self, item_name):
        # Check if it's pet-required item
        if item_name == settings.required_item:
            reward_factor = settings.FACTOR_FEED_REQ
            self.close_bubble.emit('feed_required')
        else:
            reward_factor = 1

        # 食物
        if settings.items_data.item_dict[item_name]['item_type']=='consumable':
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_item', item_name)
            self.bubble_manager.trigger_bubble('feed_done')

        # 附件物品
        elif item_name in self.pet_conf.act_name or item_name in self.pet_conf.acc_name:
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('use_clct', item_name)

        # 对话物品
        elif settings.items_data.item_dict[item_name]['item_type']=='dialogue':
            if item_name in self.pet_conf.msg_dict:
                accs = {'name':'dialogue', 'msg_dict':self.pet_conf.msg_dict[item_name]}
                x = self.pos().x() #+self.width()//2
                y = self.pos().y() #+self.height()
                self.setup_acc.emit(accs, x, y)
                return

        # 系统附件物品
        elif item_name in self.sys_conf.acc_name:
            accs = self.sys_conf.accessory_act[item_name]
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)
        
        # Subpet
        elif settings.items_data.item_dict[item_name]['item_type']=='subpet':
            pet_acc = {'name':'subpet', 'pet_name':item_name}
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(pet_acc, x, y)
            return

        else:
            pass

        # 鼠标挂件 - currently gave up :(
        '''
        elif item_name in self.sys_conf.mouseDecor:
            accs = {'name':'mouseDecor', 'config':self.sys_conf.mouseDecor[item_name]}
            x = self.pos().x()+self.width()//2
            y = self.pos().y()+self.height()
            self.setup_acc.emit(accs, x, y)
        '''
        
        # 使用物品 改变数值
        self._change_status('hp', 
                            int(settings.items_data.item_dict[item_name]['effect_HP']*reward_factor),
                            from_mod='inventory', send_note=True)
        
        if item_name in self.pet_conf.item_favorite:
            self._change_status('fv',
                                int(settings.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_favorite[item_name]*reward_factor),
                                from_mod='inventory', send_note=True)

        elif item_name in self.pet_conf.item_dislike:
            self._change_status('fv', 
                                int(settings.items_data.item_dict[item_name]['effect_FV']*self.pet_conf.item_dislike[item_name]*reward_factor),
                                from_mod='inventory', send_note=True)

        else:
            self._change_status('fv', 
                                int(settings.items_data.item_dict[item_name]['effect_FV']*reward_factor),
                                from_mod='inventory', send_note=True)

    def add_item(self, n_items, item_names=[]):
        self.addItem_toInven.emit(n_items, item_names)

    def patpat(self):
        # 摸摸动画
        if self.click_count >= 7:
            self.bubble_manager.trigger_bubble("pat_frequent")
        elif self.workers['Interaction'].interact != 'patpat':
            if settings.focus_timer_on:
                self.bubble_manager.trigger_bubble("pat_focus")
            else:
                self.workers['Animation'].pause()
                self.workers['Interaction'].start_interact('patpat')

        # 概率触发浮动的心心
        prob_num_0 = random.uniform(0, 1)
        if prob_num_0 < sys_pp_heart:
            try:
                accs = self.sys_conf.accessory_act['heart']
            except:
                return
            x = QCursor.pos().x() #self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
            y = QCursor.pos().y() #self.pos().y()+self.height()-0.8*self.label.height() + random.uniform(0, 1) * 10
            self.setup_acc.emit(accs, x, y)

        elif prob_num_0 < settings.PP_COIN:
            # Drop random amount of coins
            self.addCoins.emit(0)

        elif prob_num_0 > sys_pp_item:
            self.addItem_toInven.emit(1, [])
            #print('物品掉落！')

        if prob_num_0 > sys_pp_audio:
            #随机语音
            if random.uniform(0, 1) > 0.5:
                # This will be deprecated soon
                self.register_notification('random', '')
            else:
                self.bubble_manager.trigger_patpat_random()

    def item_drop_anim(self, item_name):
        if item_name == 'coin':
            accs = {"name":"item_drop", "item_image":[settings.items_data.coin['image']]}
        else:
            item = settings.items_data.item_dict[item_name]
            accs = {"name":"item_drop", "item_image":[item['image']]}
        x = self.pos().x()+self.width()//2 + random.uniform(-0.25, 0.25) * self.label.width()
        y = self.pos().y()+self.height()-self.label.height()
        self.setup_acc.emit(accs, x, y)



    def quit(self) -> None:
        """
        关闭窗口, 系统退出
        :return:
        """
        settings.pet_data.save_data()
        settings.pet_data.frozen()
        self.stop_thread('Animation')
        self.stop_thread('Interaction')
        self.stop_thread("Scheduler")
        self.stopAllThread.emit()
        self.close()
        sys.exit()

    def stop_thread(self, module_name):
        self.workers[module_name].kill()
        self.threads[module_name].terminate()
        self.threads[module_name].wait()
        #self.threads[module_name].wait()

    def follow_mouse_act(self):
        sender = self.sender()
        if settings.onfloor == 0:
            return
        if sender.text()==self.tr("Follow Cursor"):
            sender.setText(self.tr("Stop Follow"))
            self.MouseTracker = MouseMoveManager()
            self.MouseTracker.moved.connect(self.update_mouse_position)
            self.get_positions('mouse')
            self.workers['Animation'].pause()
            self.workers['Interaction'].start_interact('followTarget', 'mouse')
        else:
            sender.setText(self.tr("Follow Cursor"))
            self.MouseTracker._listener.stop()
            self.workers['Interaction'].stop_interact()

    def get_positions(self, object_name):

        main_pos = [int(self.pos().x() + self.width()//2), int(self.pos().y() + self.height() - self.label.height())]

        if object_name == 'mouse':
            self.send_positions.emit(main_pos, self.mouse_pos)

    def update_mouse_position(self, x, y):
        self.mouse_pos = [x, y]

    def stop_trackMouse(self):
        self.start_follow_mouse.setText(self.tr("Follow Cursor"))
        self.MouseTracker._listener.stop()

    '''
    def fall_onoff(self):
        #global set_fall
        sender = self.sender()
        if settings.set_fall==1:
            sender.setText(self.tr("Don't Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/off.svg')))
            settings.set_fall=0
        else:
            sender.setText(self.tr("Allow Drop"))
            sender.setIcon(QIcon(os.path.join(basedir,'res/icons/on.svg')))
            settings.set_fall=1
    '''

    def _show_controlPanel(self):
        self.show_controlPanel.emit()

    def _show_dashboard(self):
        self.show_dashboard.emit()

    '''
    def show_compday(self):
        sender = self.sender()
        if sender.text()=="显示陪伴天数":
            acc = {'name':'compdays', 
                   'height':self.label.height(),
                   'message': "这是%s陪伴你的第 %i 天"%(settings.petname,settings.pet_data.days)}
            sender.setText("关闭陪伴天数")
            x = self.pos().x() + self.width()//2
            y = self.pos().y() + self.height() - self.label.height() - 20 #*settings.size_factor
            self.setup_acc.emit(acc, x, y)
            self.showing_comp = 1
        else:
            sender.setText("显示陪伴天数")
            self.setup_acc.emit({'name':'compdays'}, 0, 0)
            self.showing_comp = 0
    '''

    def show_tomato(self):
        if self.tomato_window.isVisible():
            self.tomato_window.hide()

        else:
            self.tomato_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.tomato_window.width()//2),
                                    max(self.current_screen.topLeft().y(),self.pos().y()-self.tomato_window.height()))
            self.tomato_window.show()

        '''
        elif self.tomato_clock.text()=="取消番茄时钟":
            self.tomato_clock.setText("番茄时钟")
            self.workers['Scheduler'].cancel_tomato()
            self.tomatoicon.hide()
            self.tomato_time.hide()
        '''

    def run_tomato(self, nt):
        self.workers['Scheduler'].add_tomato(n_tomato=int(nt))
        self.tomatoicon.show()
        self.tomato_time.show()
        settings.focus_timer_on = True

    def cancel_tomato(self):
        self.workers['Scheduler'].cancel_tomato()

    def change_tomato_menu(self):
        self.tomatoicon.hide()
        self.tomato_time.hide()
        settings.focus_timer_on = False

    
    def show_focus(self):
        if self.focus_window.isVisible():
            self.focus_window.hide()
        
        else:
            self.focus_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.focus_window.width()//2),
                                   max(self.current_screen.topLeft().y(),self.pos().y()-self.focus_window.height()))
            self.focus_window.show()


    def run_focus(self, task, hs, ms):
        if task == 'range':
            if hs<=0 and ms<=0:
                return
            self.workers['Scheduler'].add_focus(time_range=[hs,ms])
        elif task == 'point':
            self.workers['Scheduler'].add_focus(time_point=[hs,ms])
        self.focusicon.show()
        self.focus_time.show()
        settings.focus_timer_on = True

    def pause_focus(self, state):
        if state: # 暂停
            self.workers['Scheduler'].pause_focus()
        else: # 继续
            self.workers['Scheduler'].resume_focus(int(self.focus_time.value()), int(self.focus_time.maximum()))


    def cancel_focus(self):
        self.workers['Scheduler'].cancel_focus(int(self.focus_time.maximum()-self.focus_time.value()))

    def change_focus_menu(self):
        self.focusicon.hide()
        self.focus_time.hide()
        settings.focus_timer_on = False


    def show_remind(self):
        if self.remind_window.isVisible():
            self.remind_window.hide()
        else:
            self.remind_window.move(max(self.current_screen.topLeft().y(),self.pos().x()-self.remind_window.width()//2),
                                    max(self.current_screen.topLeft().y(),self.pos().y()-self.remind_window.height()))
            self.remind_window.show()

    ''' Reminder function deleted from v0.3.7
    def run_remind(self, task_type, hs=0, ms=0, texts=''):
        if task_type == 'range':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms])
        elif task_type == 'point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms])
        elif task_type == 'repeat_interval':
            self.workers['Scheduler'].add_remind(texts=texts, time_range=[hs,ms], repeat=True)
        elif task_type == 'repeat_point':
            self.workers['Scheduler'].add_remind(texts=texts, time_point=[hs,ms], repeat=True)
    '''

    def show_inventory(self):
        if self.inventory_window.isVisible():
            self.inventory_window.hide()
        else:
            self.inventory_window.move(max(self.current_screen.topLeft().y(), self.pos().x()-self.inventory_window.width()//2),
                                    max(self.current_screen.topLeft().y(), self.pos().y()-self.inventory_window.height()))
            self.inventory_window.show()
            #print(self.inventory_window.size())

    '''
    def show_settings(self):
        if self.setting_window.isVisible():
            self.setting_window.hide()
        else:
            #self.setting_window.move(max(self.current_screen.topLeft().y(), self.pos().x()-self.setting_window.width()//2),
            #                        max(self.current_screen.topLeft().y(), self.pos().y()-self.setting_window.height()))
            #self.setting_window.resize(800,800)
            self.setting_window.show()
    '''

    '''
    def show_settingstest(self):
        self.settingUI = SettingMainWindow()
        
        if sys.platform == 'win32':
            self.settingUI.setWindowFlags(
                Qt.FramelessWindowHint | Qt.SubWindow | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        else:
            self.settingUI.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.NoDropShadowWindowHint)
        self.settingUI.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        cardShadowSE = QtWidgets.QGraphicsDropShadowEffect(self.settingUI)
        cardShadowSE.setColor(QColor(189, 167, 165))
        cardShadowSE.setOffset(0, 0)
        cardShadowSE.setBlurRadius(20)
        self.settingUI.setGraphicsEffect(cardShadowSE)
        
        self.settingUI.show()
    '''

    def runAnimation(self):
        # Create thread for Animation Module
        self.threads['Animation'] = QThread()
        self.workers['Animation'] = Animation_worker(self.pet_conf)
        self.workers['Animation'].moveToThread(self.threads['Animation'])

        # Connect signals and slots
        self.threads['Animation'].started.connect(self.workers['Animation'].run)
        self.workers['Animation'].sig_setimg_anim.connect(self.set_img)
        self.workers['Animation'].sig_move_anim.connect(self._move_customized)
        self.workers['Animation'].sig_repaint_anim.connect(self.repaint)
        self.workers['Animation'].acc_regist.connect(self.register_accessory)

        # Start the thread
        self.threads['Animation'].start()
        self.threads['Animation'].setTerminationEnabled()


    def hpchange(self, hp_tier, direction):
        self.workers['Animation'].hpchange(hp_tier, direction)
        self.hptier_changed_main_note.emit(hp_tier, direction)
        #self._update_statusTitle(hp_tier)

    def fvchange(self, fv_lvl):
        if fv_lvl == -1:
            self.fvlvl_changed_main_note.emit(fv_lvl)
        else:
            self.workers['Animation'].fvchange(fv_lvl)
            self.fvlvl_changed_main_note.emit(fv_lvl)
            self.fvlvl_changed_main_inve.emit(fv_lvl)
            self._update_fvlock()
            self.lvl_badge.set_level(fv_lvl)
        self.refresh_acts.emit()
        self.bubble_manager.trigger_bubble(bb_type="fv_lvlup")

    def runInteraction(self):
        # Create thread for Interaction Module
        self.threads['Interaction'] = QThread()
        self.workers['Interaction'] = Interaction_worker(self.pet_conf)
        self.workers['Interaction'].moveToThread(self.threads['Interaction'])

        # Connect signals and slots
        self.workers['Interaction'].sig_setimg_inter.connect(self.set_img)
        self.workers['Interaction'].sig_move_inter.connect(self._move_customized)
        self.workers['Interaction'].sig_act_finished.connect(self.resume_animation)
        self.workers['Interaction'].sig_interact_note.connect(self.register_notification)
        self.workers['Interaction'].acc_regist.connect(self.register_accessory)
        self.workers['Interaction'].query_position.connect(self.get_positions)
        self.workers['Interaction'].stop_trackMouse.connect(self.stop_trackMouse)
        self.send_positions.connect(self.workers['Interaction'].receive_pos)

        # Start the thread
        self.threads['Interaction'].start()
        self.threads['Interaction'].setTerminationEnabled()

    def runScheduler(self):
        # Create thread for Scheduler Module
        self.threads['Scheduler'] = QThread()
        self.workers['Scheduler'] = Scheduler_worker()
        self.workers['Scheduler'].moveToThread(self.threads['Interaction'])

        # Connect signals and slots
        self.threads['Scheduler'].started.connect(self.workers['Scheduler'].run)
        self.workers['Scheduler'].sig_settext_sche.connect(self.register_notification) #_set_dialogue_dp)
        self.workers['Scheduler'].sig_setact_sche.connect(self._show_act)
        self.workers['Scheduler'].sig_setstat_sche.connect(self._change_status)
        self.workers['Scheduler'].sig_focus_end.connect(self.change_focus_menu)
        self.workers['Scheduler'].sig_tomato_end.connect(self.change_tomato_menu)
        self.workers['Scheduler'].sig_settime_sche.connect(self._change_time)
        self.workers['Scheduler'].sig_addItem_sche.connect(self.add_item)
        self.workers['Scheduler'].sig_setup_bubble.connect(self._process_greeting_mssg)

        # Start the thread
        self.threads['Scheduler'].start()
        self.threads['Scheduler'].setTerminationEnabled()



    def _move_customized(self, plus_x, plus_y):

        #print(act_list)
        #direction, frame_move = str(act_list[0]), float(act_list[1])
        pos = self.pos()
        new_x = pos.x() + plus_x
        new_y = pos.y() + plus_y

        # 正在下落的情况，可以切换屏幕
        if settings.onfloor == 0:
            # 落地情况
            if new_y > self.floor_pos+settings.current_anchor[1]:
                settings.onfloor = 1
                new_x, new_y = self.limit_in_screen(new_x, new_y)
            # 在空中
            else:
                anim_area = QRect(self.pos() + QPoint(self.width()//2-self.label.width()//2, 
                                                      self.height()-self.label.height()), 
                                  QSize(self.label.width(), self.label.height()))
                intersected = self.current_screen.intersected(anim_area)
                area = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                if area > 0.5:
                    pass
                    #new_x, new_y = self.limit_in_screen(new_x, new_y)
                else:
                    switched = False
                    for screen in settings.screens:
                        if screen.geometry() == self.current_screen:
                            continue
                        intersected = screen.geometry().intersected(anim_area)
                        area_tmp = intersected.width() * intersected.height() / self.label.width() / self.label.height()
                        if area_tmp > 0.5:
                            self.switch_screen(screen)
                            switched = True
                    if not switched:
                        new_x, new_y = self.limit_in_screen(new_x, new_y)

        # 正在做动作的情况，局限在当前屏幕内
        else:
            new_x, new_y = self.limit_in_screen(new_x, new_y, on_action=True)

        self.move(new_x, new_y)


    def switch_screen(self, screen):
        self.current_screen = screen.geometry()
        settings.current_screen = screen
        self.screen_geo = screen.availableGeometry() #screenGeometry()
        self.screen_width = self.screen_geo.width()
        self.screen_height = self.screen_geo.height()
        self.floor_pos = self.current_screen.topLeft().y() + self.screen_height -self.height()


    def limit_in_screen(self, new_x, new_y, on_action=False):
        # 超出当前屏幕左边界
        if new_x+self.width()//2 < self.current_screen.topLeft().x():
            #surpass_x = 'Left'
            new_x = self.current_screen.topLeft().x()-self.width()//2
            if not on_action:
                settings.dragspeedx = -settings.dragspeedx * settings.SPEED_DECAY
                settings.fall_right = not settings.fall_right

        # 超出当前屏幕右边界
        elif new_x+self.width()//2 > self.current_screen.topLeft().x() + self.screen_width:
            #surpass_x = 'Right'
            new_x = self.current_screen.topLeft().x() + self.screen_width-self.width()//2
            if not on_action:
                settings.dragspeedx = -settings.dragspeedx * settings.SPEED_DECAY
                settings.fall_right = not settings.fall_right

        # 超出当前屏幕上边界
        if new_y+self.height()-self.label.height()//2 < self.current_screen.topLeft().y():
            #surpass_y = 'Top'
            new_y = self.current_screen.topLeft().y() + self.label.height()//2 - self.height()
            if not on_action:
                settings.dragspeedy = abs(settings.dragspeedy) * settings.SPEED_DECAY

        # 超出当前屏幕下边界
        elif new_y > self.floor_pos+settings.current_anchor[1]:
            #surpass_y = 'Bottom'
            new_y = self.floor_pos+settings.current_anchor[1]

        return new_x, new_y


    def _show_act(self, act_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('actlist', act_name)
    '''
    def _show_acc(self, acc_name):
        self.workers['Animation'].pause()
        self.workers['Interaction'].start_interact('anim_acc', acc_name)
    '''
    def _set_defaultAct(self, act_name):

        if act_name == settings.defaultAct[self.curr_pet_name]:
            settings.defaultAct[self.curr_pet_name] = None
            settings.save_settings()
            for action in self.defaultAct_menu.menuActions():
                if action.text() == act_name:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dot.png')))
        else:
            for action in self.defaultAct_menu.menuActions():
                if action.text() == settings.defaultAct[self.curr_pet_name]:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dot.png')))
                elif action.text() == act_name:
                    action.setIcon(QIcon(os.path.join(basedir, 'res/icons/dotfill.png'))) #os.path.join(basedir, 'res/icons/check_icon.png')))

            settings.defaultAct[self.curr_pet_name] = act_name
            settings.save_settings()


    def resume_animation(self):
        self.workers['Animation'].resume()
    
    def _mightEventTrigger(self):
        # Update date
        settings.pet_data.update_date()
        if hasattr(self, "daysLabel"):
            self.daysLabel.setText(" EchoPet Demo")




def _load_all_pic(pet_name: str) -> dict:
    """
    加载宠物所有动作图片
    :param pet_name: 宠物名称
    :return: {动作编码: 动作图片}
    """
    img_dir = os.path.join(basedir, 'res/role/{}/action/'.format(pet_name))
    images = os.listdir(img_dir)
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}

def _get_q_img(img_path: str) -> QPixmap:
    """
    将图片路径加载为 QPixmap
    :param img_path: 图片路径
    :return: QPixmap
    """
    #image = QImage()
    image = QPixmap()
    image.load(img_path)
    return image

def _build_act(name: str, parent: QObject, act_func, icon=None) -> Action:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    if icon:
        act = Action(icon, name, parent)
    else:
        act = Action(name, parent)
    act.triggered.connect(lambda: act_func(name))
    return act

def _build_act_param(name: str, param: str, parent: QObject, act_func) -> Action:
    """
    构建改变菜单动作
    :param pet_name: 菜单动作名称
    :param parent 父级菜单
    :param act_func: 菜单动作函数
    :return:
    """
    act = Action(name, parent)
    act.triggered.connect(lambda: act_func(param))
    return act
