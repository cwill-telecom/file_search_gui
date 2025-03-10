# This app searches a directory(folder) for a filetype 
# It also allows you to save all the found to a seperate folder


import os
import csv
import datetime
import shutil
import wx

class FileSearchApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(FileSearchApp, self).__init__(*args, **kw)
        
        self.InitUI()
        
    def InitUI(self):
        panel = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Directory picker for selecting the location to search
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        st0 = wx.StaticText(panel, label='Select the directory to search:')
        hbox0.Add(st0, flag=wx.RIGHT, border=8)
        self.dir_picker = wx.DirPickerCtrl(panel, message="Select a directory")
        hbox0.Add(self.dir_picker, proportion=1)
        vbox.Add(hbox0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # File type input
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Enter the file type (e.g., .pdf, .txt):')
        hbox1.Add(st1, flag=wx.RIGHT, border=8)
        self.file_type_input = wx.TextCtrl(panel)
        hbox1.Add(self.file_type_input, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Search button
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.search_btn = wx.Button(panel, label='Search')
        hbox2.Add(self.search_btn, flag=wx.LEFT, border=10)
        vbox.Add(hbox2, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=10)
        
        # Copy files checkbox
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.copy_files_chk = wx.CheckBox(panel, label='Copy found files to a separate folder')
        hbox3.Add(self.copy_files_chk, flag=wx.LEFT, border=10)
        vbox.Add(hbox3, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=10)
        
        # Results display
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.result_area = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        hbox4.Add(self.result_area, proportion=1, flag=wx.EXPAND)
        vbox.Add(hbox4, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        self.search_btn.Bind(wx.EVT_BUTTON, self.OnSearch)
        
        self.SetSize((500, 400))
        self.SetTitle('File Search Application')
        self.Centre()
    
    def OnSearch(self, event):
        file_type = self.file_type_input.GetValue().strip()
        directory_to_search = self.dir_picker.GetPath()
        
        if not file_type.startswith('.'):
            file_type = '.' + file_type
        
        if not os.path.isdir(directory_to_search):
            wx.MessageBox("Please select a valid directory.", "Error", wx.OK | wx.ICON_ERROR)
            return
        
        found_files = self.search_files(directory_to_search, file_type)
        
        if found_files:
            self.result_area.SetValue(f"{len(found_files)} {file_type.upper()} files found.")
            output_file = f"{file_type.strip('.')}_file_list.csv"
            self.write_to_csv(found_files, output_file)
            self.result_area.AppendText(f"\n{file_type.upper()} file names, locations, and creation dates have been written to {output_file}")
            
            if self.copy_files_chk.GetValue():
                destination_folder = os.path.join(os.getcwd(), f"copied_{file_type.strip('.').lower()}_files")
                self.copy_files(found_files, destination_folder)
                self.result_area.AppendText(f"\nFiles have been copied to {destination_folder}")
        else:
            self.result_area.SetValue(f"No {file_type.upper()} files found.")
    
    def search_files(self, directory, file_extension):
        found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    found_files.append((file_path, os.path.getctime(file_path)))
        found_files.sort(key=lambda x: x[1])  # Sort by creation time
        return found_files

    def write_to_csv(self, found_files, output_file):
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['File Location', 'File Name', 'Creation Date'])
            for found_file in found_files:
                file_path, creation_date = found_file
                file_location, file_name = os.path.split(file_path)
                creation_date = datetime.datetime.fromtimestamp(creation_date).strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([file_location, file_name, creation_date])

    def copy_files(self, found_files, destination_folder):
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        for found_file in found_files:
            file_path, _ = found_file
            shutil.copy(file_path, destination_folder)


def main():
    app = wx.App(False)
    frame = FileSearchApp(None)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
