#!/usr/bin/env python3

import config

import csv
import datetime
import struct
import threading
import serial
import serial.tools.list_ports
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
      
class Handler:
	def on_destroy(self, *args):
		thread_read.work = False
		thread_read.exit = True
		thread_read.join()
		disconnect()
		Gtk.main_quit()
		return

	def on_GtkEntry_icon(self, *args):
		args[0].set_text("")
		return

	def on_ports_reload(self, *args):
		load_ports()
		return

	def on_settings_save(self, *args):
		save_settings()
		return
	
	def on_arduino_save(self, *args):
		distance = float(GtkSpinButton_distance.get_value())
		scale_iter = GtkComboBox_scales.get_active_iter()
		if scale_iter is not None:
			scales_model = GtkComboBox_scales.get_model()
			factor = float(scales_model.get_value(scale_iter, 2))
		else:
			factor = float(0.0)
		sensitivity = int(GtkSpinButton_sensitivity.get_value())
		send = "<change," + str(distance) + "," + str(factor) + "," + str(sensitivity) + ">"
		ser.write(str.encode(send))
		return

	def on_arduino_reload(self, *args):
		load_arduino()
		return

	def on_GtkButton_file_clicked(self, *args):
		dialog = Gtk.FileChooserDialog("Datei auswählen ...", GtkWindow_window, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		filter_dat = Gtk.FileFilter()
		filter_dat.set_name("DAT-Dateien")
		filter_dat.add_pattern("*.dat")
		dialog.add_filter(filter_dat)
		filter_any = Gtk.FileFilter()
		filter_any.set_name("Alle Dateien")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)
		response = dialog.run()
		if response == Gtk.ResponseType.OK:
			GtkEntry_file.set_text(dialog.get_filename())
		dialog.destroy()
		return
		
	def on_settings_reset(self, *args):
		load_ports()
		load_filename()
		return
		
	def on_arduino_reset(self, *args):
		load_arduino()
		return
	
	def on_connect(self, *args):
		connect(port)
		return
	
	def on_disconnect(self, *args):
		disconnect()
		return
	
	def history_changed(self, *args):
		with open(filename, 'w', newline='') as csvfile:
			fieldnames = ['date', 'speed','loco']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			history = GtkTreeView_history.get_model()
			for row in history:
				writer.writerow({'date': row[0], 'speed': row[1], 'loco': row[2]})
		return
	
	def loco_changed(self,cell, path, new_text, data=None):
		loco_model = GtkTreeView_history.get_model()
		loco_iter = loco_model.get_iter(path)
		loco_model.set_value(loco_iter, 2, new_text)
		return

def save_settings():
	disconnect()
	port_iter = GtkComboBox_ports.get_active_iter()
	if port_iter is not None:
		ports_model = GtkComboBox_ports.get_model()
		selected_port = ports_model.get_value(port_iter, 0)
	config.write(Port = selected_port, Filename = GtkEntry_file.get_text())
	port = selected_port
	filename = GtkEntry_file.get_text()
	load_history()
	connect(port)

def load_ports():
	GtkListStore_ports.clear()
	ports_list = serial.tools.list_ports.comports()
	saved_port = config.read("Port")
	for ports in sorted(ports_list):
		iter = GtkListStore_ports.append([ports.device, ports.description])
		if ports.device == saved_port:
			GtkComboBox_ports.set_active_iter(iter)
	return

def load_filename():
	GtkEntry_file.set_text(config.read("Filename"))
	return

def load_distance(arg):
	GtkSpinButton_distance.set_value(float(arg))
	return

def load_sensitivity(arg):
	GtkSpinButton_sensitivity.set_value(int(arg))
	return

def load_scale(arg):
	scales_list = GtkComboBox_scales.get_model()
	for i in range(len(scales_list)):
		if float(arg) == scales_list[i][2]:
			GtkComboBox_scales.set_active(i)
	return

def load_arduino():
	ser.write(b'<settings>')
	return

def connect(port):
	GtkLabel_connection.set_text("verbinden...")
	try:
		ser.port = port
		ser.open()
		serial_thread(True)
		if ser.is_open:
			GtkLabel_connection.set_text("verbunden")
			activate_arduino_panel(True)
		else:
			disconnect()
	except:
		disconnect()
		GtkLabel_connection.set_text("Verbindungsfehler")
	return

def disconnect():
	serial_thread(False)
	ser.close()
	activate_arduino_panel(False)
	GtkLabel_connection.set_text("getrennt")
	return

def serial_thread(arg):
	if arg:
		thread_read.work = True
	else:
		thread_read.work = False
	return

def serial_read():
	while not getattr(thread_read, "exit", False):
		while getattr(thread_read, "work", True):
			if ser.in_waiting > 0:
				incoming = ser.readline()
				message = incoming.decode("utf-8")[1:-3]
				
				#print(message) # nur für debug, danach entwerten
								
				if "settings" in message:
					message = message.split(',')
					load_distance(message[1])
					load_scale(message[2])
					load_sensitivity(message[3])
				
				if "display" in message:
					message = message.split(',')
					first_line = message[1]
					second_line = message[2]
					GtkLabel_display.set_text(message[1] + "\n" + message [2])
					if message[1] == "Geschwindigkeit:":
						log(message[2])
						pass
					
	return

def log(value):
	now = datetime.datetime.now().strftime("%d.%m.%Y - %H:%M")
	GtkListStore_history.append([str(now), value,""])
	return

def load_history():
	GtkListStore_history.clear()
	try:
		with open(filename, newline='') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				GtkListStore_history.append([row['date'], row['speed'], row['loco']])
	except:
		pass
	return

def activate_arduino_panel(arg):
	GtkSpinButton_distance.set_sensitive(arg)
	GtkComboBox_scales.set_sensitive(arg)
	GtkButton_distance.set_sensitive(arg)
	GtkButton_scale.set_sensitive(arg)
	GtkButton_arduino_save.set_sensitive(arg)
	GtkButton_arduino_reset.set_sensitive(arg)
	GtkSpinButton_sensitivity.set_sensitive(arg)
	GtkButton_sensitivity.set_sensitive(arg)
	return

builder = Gtk.Builder()
builder.add_from_file("pySpeed.glade")
builder.connect_signals(Handler())

GtkWindow_window = builder.get_object("GtkWindow_window")
GtkComboBox_ports = builder.get_object("GtkComboBox_ports")
GtkComboBox_scales = builder.get_object("GtkComboBox_scales")
GtkSpinButton_distance = builder.get_object("GtkSpinButton_distance")
GtkEntry_ports = builder.get_object("GtkEntry_ports")
GtkEntry_scales = builder.get_object("GtkEntry_scales")
GtkListStore_ports = builder.get_object("GtkListStore_ports")
GtkListStore_scales = builder.get_object("GtkListStore_scales")
GtkListStore_history = builder.get_object("GtkListStore_history")
GtkEntry_file = builder.get_object("GtkEntry_file")
GtkLabel_connection = builder.get_object("GtkLabel_connection")
GtkButton_distance = builder.get_object("GtkButton_distance")
GtkButton_scale = builder.get_object("GtkButton_scale")
GtkButton_sensitivity = builder.get_object("GtkButton_sensitivity")
GtkSpinButton_sensitivity = builder.get_object("GtkSpinButton_sensitivity")
GtkButton_arduino_save = builder.get_object("GtkButton_arduino_save")
GtkButton_arduino_reset = builder.get_object("GtkButton_arduino_reset")
GtkLabel_display = builder.get_object("GtkLabel_display")
GtkTreeView_history = builder.get_object("GtkTreeView_history")

GtkWindow_window.show_all()

ser = serial.Serial()
ser.baudrate = 9600
load_ports()
port = config.read("Port")
load_filename()
filename = config.read("Filename")
thread_read = threading.Thread(target=serial_read,)
thread_read.work = False
thread_read.start()

load_history()

connect(port)

Gtk.main()
