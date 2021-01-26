# coding: utf-8

from model import Model
from view import View

import threading

from gi.repository import GLib
import time


class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View(self)

    def request_workout_list(self):
        return self.model.get_workout_list()

    def open_step_list(self, widget, row, col, view):
        if not view.workout_spinner.is_visible():
            name = widget.get_model()[row][1]
            view.view_step_list(name)
            threading.Thread(target=self.load_step_list,
                             args=[name, self.model, view]).start()

    def load_step_list(self, name, model, view):
        try:
            step_list = model.get_steps_of(name)
        except Exception as ex:
            GLib.idle_add(view.handle_error, ex)
        GLib.idle_add(view.load_step_list, step_list)

    def open_workout_tree(self, widget, view):
        view.view_workout_tree()
        threading.Thread(target=self.load_workout_tree,
                         args=[self.model, view]).start()

    def load_workout_tree(self, model, view):
        try:
            workouts = model.get_workout_list()
        except Exception as ex:
            GLib.idle_add(view.handle_error, ex)
        GLib.idle_add(view.load_workout_tree, workouts)

    def workout_cursor_changed(self, widget, view):
        view.delete_button.set_sensitive(
            view.get_selected_workout() is not None
            and not view.workout_spinner.is_visible())

    def delete_workout(self, widget, view):
        received_tuple = view.get_selected_workout()
        workout = received_tuple[0]
        iterator = received_tuple[1]
        self.delete_enabled = False
        view.delete_button.set_sensitive(False)
        view.workout_spinner.show()
        threading.Thread(target=self.request_deletion,
                         args=[workout, iterator, self.model, view]).start()

    def request_deletion(self, workout, iterator,  model, view):
        model.delete_workout(workout)
        GLib.idle_add(view.show_deletion, workout, iterator)

    def move_step_up(self, widget, view):
        row = widget.get_parent().get_parent().get_parent()
        index = row.get_index()
        parent = row.get_parent()

        if index == 0:
            parent.remove(row)
            parent.insert(row, -1)
        else:
            parent.remove(row)
            parent.insert(row, index - 1)

    def move_step_down(self, widget, view):
        row = widget.get_parent().get_parent().get_parent()
        index = row.get_index()
        parent = row.get_parent()
        last = len(parent.get_children())

        if index == last - 1:
            parent.remove(row)
            parent.insert(row, 0)
        else:
            parent.remove(row)
            parent.insert(row, index + 1)
