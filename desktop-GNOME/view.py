#coding: utf-8

from pathlib import Path
import base64
import gi
import gettext
import locale
from datetime import datetime

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf


class View:
    def __init__(self, controller):
        self.controller = controller

        # Set localization tools for spanish
        self.locale_setting = locale.getlocale()
        if self.locale_setting[0] == 'es_ES':
            es_ES = gettext.translation(
                'es_ES', localedir='locale', languages=['es'])
            es_ES.install()
        else:
            en_US = gettext.translation(
                'en_US', localedir='locale', languages=['en'])
            en_US.install()

        # Build workout_tree_win
        self.workout_tree = WorkoutTree()
        self.workout_tree.view.connect(
            'row-activated', controller.open_step_list, self)

        self.workout_tree_win = Gtk.ScrolledWindow()
        self.workout_tree_win.set_policy(Gtk.PolicyType.NEVER,
                                         Gtk.PolicyType.ALWAYS)
        self.workout_tree_win.add(self.workout_tree.view)

        self.workout_tree_header = Gtk.HeaderBar(
            show_close_button=True, title=_('IPM P1'), subtitle=_('Workouts List'))
        self.delete_button = Gtk.Button(_('Remove'))
        self.delete_button.get_style_context().add_class(
            Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.delete_button.connect(
            'clicked', self.controller.delete_workout, self)
        self.workout_tree_header.pack_end(self.delete_button)
        self.workout_tree.view.connect(
            'cursor-changed', self.controller.workout_cursor_changed, self)

        self.workout_spinner = Gtk.Spinner()
        self.workout_spinner.set_margin_left(6)
        self.workout_spinner.start()
        self.workout_tree_header.pack_start(self.workout_spinner)

        # Build step_list
        self.step_list = WorkoutStepList()
        self.step_list_header = Gtk.HeaderBar(
            show_close_button=True, title=_('IPM P1'))
        self.back_button = Gtk.Button('<')
        self.back_button.connect(
            'clicked', self.controller.open_workout_tree, self)
        self.step_list_header.pack_start(self.back_button)
        self.step_spinner = Gtk.Spinner()
        self.step_spinner.start()
        self.step_spinner.hide()
        self.step_spinner.set_margin_left(6)
        self.step_list_header.pack_start(self.step_spinner)

        self.step_list_win = Gtk.ScrolledWindow()

        # Set up the initial main window
        self.main_win = Gtk.Window(title=_('IPM P1'))
        self.main_win.set_titlebar(self.workout_tree_header)
        self.main_win.set_default_size(0, 480)
        self.main_win.connect('destroy', Gtk.main_quit)
        self.main_win.show_all()

        self.controller.open_workout_tree(None, self)

        Gtk.main()

    def view_workout_tree(self):
        self.delete_button.set_sensitive(False)
        self.main_win.set_titlebar(self.workout_tree_header)
        # If not the first time opening workout tree (1 is the headerbar)
        if len(self.main_win.get_children()) != 1:
            self.main_win.remove(self.step_list_win)

        self.main_win.add(self.workout_tree_win)
        self.main_win.show_all()
        self.workout_tree_win.hide()

    def load_workout_tree(self, workouts):
        self.workout_tree.update(workouts)
        self.workout_spinner.hide()
        self.workout_tree_win.show()
        self.step_spinner.hide()

    def get_selected_workout(self):
        iterator = self.workout_tree.view.get_selection().get_selected()[1]
        if iterator is None:
            return None
        return (self.workout_tree.model.get_value(iterator, 1), iterator)

    def view_step_list(self, workout_name):
        self.step_list_header.set_subtitle(
            _('Exercise list for ') + workout_name)
        self.main_win.set_titlebar(self.step_list_header)

        self.step_list_win.set_policy(Gtk.PolicyType.NEVER,
                                      Gtk.PolicyType.ALWAYS)

        self.main_win.remove(self.workout_tree_win)
        self.main_win.show_all()
        self.back_button.hide()

    def load_step_list(self, step_list):
        self.back_button.show()
        # If there is an old ListBox, remove it
        if self.step_list_win.get_child() is not None:
            self.step_list_win.remove(self.step_list.box)
        self.step_list.update(step_list, self.controller, self)
        self.step_list_win.add(self.step_list.box)
        self.main_win.add(self.step_list_win)
        self.main_win.show_all()
        self.step_spinner.hide()

    def show_deletion(self, workout_name, iterator):
        self.workout_spinner.hide()
        self.workout_tree.model.remove(iterator)
        self.controller.workout_cursor_changed(None, self)
        self.dialog = DeletionDialog(self.main_win, workout_name)
        self.dialog.run()
        self.dialog.destroy()

    def handle_error(self, ex):
        error_dialog = ErrorDialog(self.main_win, ex)
        error_dialog.run()
        error_dialog.destroy()

    @staticmethod
    def generate_pixbuf(b64_data, size):
        if b64_data is None:
            b64_data = b''
        data = base64.b64decode(b64_data)
        if data != b'':
            img_path = Path('img/temp')
            img_path.write_bytes(data)
        else:
            img_path = Path('img/default.png')

        pixbuf_big = GdkPixbuf.Pixbuf.new_from_file(str(img_path))
        return pixbuf_big.scale_simple(size, size, GdkPixbuf.InterpType(2))
        # Type 2 is bilinear filtering, a good balance between quality
        # and speed


class WorkoutTree:
    def __init__(self):
        headers = [_('Image'), _('Name'), _('Publication date')]

        self.view = Gtk.TreeView()

        cell0 = Gtk.CellRendererPixbuf.new()
        cell1 = Gtk.CellRendererText()
        cell2 = Gtk.CellRendererText()

        col0 = Gtk.TreeViewColumn(headers[0], cell0, pixbuf=0)
        col1 = Gtk.TreeViewColumn(headers[1], cell1, text=1)
        col2 = Gtk.TreeViewColumn(headers[2], cell2, text=2)

        self.view.append_column(col0)
        self.view.append_column(col1)
        self.view.append_column(col2)

    def update(self, workouts):
        self.model = self.store_from_list(workouts)
        self.view.set_model(self.model)

    @staticmethod
    def store_from_list(workouts):
        store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        for workout in workouts:
            if workout.date is not None:
                date = datetime.strftime(workout.date, '%x')
            else:
                date = None
            store.append((View.generate_pixbuf(workout.image, 64),
                          workout.name, date))
        return store


class WorkoutStepList:
    def __init__(self):
        self.box = Gtk.ListBox()

    def reset(self):
        self.box = Gtk.ListBox()

    def update(self, step_list, controller, view):
        self.box = Gtk.ListBox()
        for step in step_list:
            if step.step_type == 'Exercise':
                self.box.add(ExerciseView(step, controller, view).box)
            else:
                self.box.add(RestView(step, controller, view).box)


class ExerciseView:
    def __init__(self, model, controller, view):

        self.box = Gtk.ListBoxRow()
        # https://developer.gnome.org/hig/stable/visual-layout.html.en
        self.view = view
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(False)
        self.grid.set_row_homogeneous(False)

        pixbuf = View.generate_pixbuf(model.image, 128)
        self.image = Gtk.Image.new_from_pixbuf(pixbuf)
        self.image.set_padding(12, 12)
        self.grid.attach(self.image, 0, 0, 1, 3)

        self.name = Gtk.Label()
        self.name.set_markup('<big>' + model.name + '</big>')
        self.name.set_halign(Gtk.Align(1))
        self.name.set_padding(12, 18)
        self.grid.attach(self.name, 1, 0, 1, 1)

        if model.duration is not None:
            duration = Gtk.Label(model.duration)
        else:
            duration = Gtk.Label(_('Duration not available'))

        duration.set_halign(Gtk.Align(1))
        duration.set_padding(12, 0)
        self.grid.attach(duration, 1, 1, 1, 1)

        video_label = Gtk.Label()
        if model.video is not None:
            video_label.set_markup(
                '<a href="' + model.video + '" title="'
                + model.video + '">' + _('Video') + '</a>')
        else:
            video_label.set_text(_('Video not avaiable'))
        video_label.set_halign(Gtk.Align(1))
        video_label.set_padding(12, 18)
        self.grid.attach(video_label, 1, 2, 1, 1)

        self.up_button = Gtk.Button(_('Move up'))
        self.up_button.connect('clicked', controller.move_step_up, self.view)
        self.up_button.set_margin_right(24)
        self.up_button.set_margin_top(12)

        self.subgrid = Gtk.Grid()
        self.subgrid.attach(self.up_button, 0, 0, 1, 1)

        self.down_button = Gtk.Button(_('Move down'))
        self.down_button.connect(
            'clicked', controller.move_step_down, self.view)

        self.down_button.set_margin_right(24)
        self.subgrid.attach(self.down_button, 0, 1, 1, 1)

        self.grid.attach(self.subgrid, 3, 0, 1, 1)

        whitespace = Gtk.Box()
        whitespace.set_hexpand(True)
        self.grid.attach(whitespace, 2, 0, 1, 3)

        self.description = Gtk.Label()
        if model.description is not None:
            self.description.set_markup(model.description)
        else:
            self.description.set_markup(
                '<big>' + _('Description unavailable') + '</big>')
        self.description.set_line_wrap(True)
        self.description.set_padding(12, 0)
        self.description.set_halign(Gtk.Align(1))
        self.description.set_justify(Gtk.Justification.FILL)
        self.description.set_margin_bottom(12)
        self.grid.attach(self.description, 0, 3, 4, 1)
        self.box.add(self.grid)


class RestView:
    def __init__(self, model, controller, view):
        self.box = Gtk.ListBoxRow()
        self.grid = Gtk.Grid()
        self.box.add(self.grid)

        self.label = Gtk.Label()
        self.label.set_markup('<big>' + _('Rest') + '</big>')
        self.label.set_padding(10, 20)
        self.grid.attach(self.label, 0, 0, 1, 1)

        self.up_button = Gtk.Button(_('Move up'))
        self.up_button.connect('clicked', controller.move_step_up, view)

        self.up_button.set_margin_right(24)
        self.up_button.set_margin_top(2)

        self.subgrid = Gtk.Grid()
        self.subgrid.attach(self.up_button, 0, 0, 1, 1)

        self.down_button = Gtk.Button(_('Move down'))
        self.down_button.connect('clicked', controller.move_step_down, view)
        self.down_button.set_margin_right(24)
        self.subgrid.attach(self.down_button, 0, 1, 1, 1)

        self.grid.attach(self.subgrid, 3, 0, 1, 1)

        self.duration = Gtk.Label()
        self.duration.set_markup('<big>' + model.duration + '</big>')
        self.grid.attach(self.duration, 1, 0, 1, 1)

        whitespace = Gtk.Box()
        whitespace.set_hexpand(True)
        self.grid.attach(whitespace, 2, 0, 1, 1)


class DeletionDialog(Gtk.Dialog):
    def __init__(self, parent, workout_name):
        Gtk.Dialog.__init__(self, _("Notification"), parent, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)

        self.label = Gtk.Label(_('You have deleted') + workout_name)

        box = self.get_content_area()
        box.add(self.label)
        self.show_all()


class ErrorDialog(Gtk.Dialog):
    def __init__(self, parent, ex):
        Gtk.Dialog.__init__(self, _("Error"), parent, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)

        self.label = Gtk.Label(ex)

        box = self.get_content_area()
        box.add(self.label)
        self.show_all()
