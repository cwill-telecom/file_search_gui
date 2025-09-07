import os
import hashlib
import shutil
import csv
import wx
from collections import defaultdict

class FileSearchApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(FileSearchApp, self).__init__(*args, **kw)
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Directory Picker
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(wx.StaticText(panel, label='Select directory to search:'), flag=wx.RIGHT, border=8)
        self.dir_picker = wx.DirPickerCtrl(panel, message="Select a directory")
        hbox0.Add(self.dir_picker, proportion=1)
        vbox.Add(hbox0, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # File Type Entry
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label='Enter file type (e.g. .txt, .pdf):'), flag=wx.RIGHT, border=8)
        self.file_type_input = wx.TextCtrl(panel)
        hbox1.Add(self.file_type_input, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Checkboxes
        self.copy_files_chk = wx.CheckBox(panel, label='Copy found files to a separate folder')
        self.detect_dups_chk = wx.CheckBox(panel, label='Detect duplicate files')
        self.hash_compare_chk = wx.CheckBox(panel, label='Use content hash (SHA256) for duplicate detection')
        self.delete_dups_chk = wx.CheckBox(panel, label='Delete duplicate files (keep one)')
        vbox.Add(self.copy_files_chk, flag=wx.LEFT|wx.TOP, border=10)
        vbox.Add(self.detect_dups_chk, flag=wx.LEFT|wx.TOP, border=10)
        vbox.Add(self.hash_compare_chk, flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=30)
        vbox.Add(self.delete_dups_chk, flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=10)

        # Output format choice
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(panel, label='Output format:'), flag=wx.RIGHT, border=8)
        self.format_choice = wx.Choice(panel, choices=["CSV", "HTML"])
        self.format_choice.SetSelection(0)  # default to CSV
        hbox2.Add(self.format_choice, proportion=1)
        vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Progress bar
        self.progress = wx.Gauge(panel, range=100, size=(250, 20))
        vbox.Add(self.progress, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Search button
        self.search_btn = wx.Button(panel, label='Search')
        self.search_btn.Bind(wx.EVT_BUTTON, self.OnSearch)
        vbox.Add(self.search_btn, flag=wx.ALIGN_LEFT|wx.ALL, border=10)

        # Results box
        self.result_area = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY)
        vbox.Add(self.result_area, proportion=1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        self.SetSize((700, 600))
        self.SetTitle('File Search with Duplicate Detection')
        self.Centre()

    def OnSearch(self, event):
        self.result_area.Clear()
        directory = self.dir_picker.GetPath()
        file_type = self.file_type_input.GetValue().strip()
        copy_files = self.copy_files_chk.GetValue()
        detect_dups = self.detect_dups_chk.GetValue()
        use_hash = self.hash_compare_chk.GetValue()
        delete_dups = self.delete_dups_chk.GetValue()
        output_format = self.format_choice.GetStringSelection().lower()  # "csv" or "html"

        if not directory or not file_type:
            self.result_area.AppendText("Please select a directory and file type.\n")
            return

        found_files = []
        hash_map = defaultdict(list)
        name_map = defaultdict(list)

        # Count total for progress bar
        total_files = sum(len(files) for _, _, files in os.walk(directory))
        processed = 0

        for root, _, files in os.walk(directory):
            for file in files:
                processed += 1
                self.progress.SetValue(int((processed / total_files) * 100))
                wx.Yield()

                if file.lower().endswith(file_type.lower()):
                    full_path = os.path.join(root, file)
                    found_files.append(full_path)

                    if detect_dups:
                        if use_hash:
                            try:
                                with open(full_path, 'rb') as f:
                                    file_hash = hashlib.sha256(f.read()).hexdigest()
                                hash_map[file_hash].append(full_path)
                            except Exception:
                                self.result_area.AppendText(f"Hash error: {file}\n")
                        else:
                            name_map[file].append(full_path)

        # Copy files if enabled
        if copy_files:
            copy_dir = os.path.join(directory, "copied_files")
            os.makedirs(copy_dir, exist_ok=True)
            for path in found_files:
                shutil.copy2(path, copy_dir)
            self.result_area.AppendText(f"\nCopied {len(found_files)} files to {copy_dir}\n")

        # Handle duplicates
        duplicate_groups = []
        if detect_dups:
            dup_source = hash_map if use_hash else name_map
            for key, paths in dup_source.items():
                if len(paths) > 1:
                    duplicate_groups.append(paths)
                    self.result_area.AppendText(f"\n[Duplicate Group]\n")
                    for p in paths:
                        self.result_area.AppendText(f"{p}\n")
                    if delete_dups:
                        for p in paths[1:]:
                            try:
                                os.remove(p)
                                self.result_area.AppendText(f"Deleted: {p}\n")
                            except Exception as e:
                                self.result_area.AppendText(f"Error deleting {p}: {e}\n")

        # Export results
        if output_format == "csv":
            csv_file = os.path.join(directory, "file_search_results.csv")
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["File Path", "Size (Bytes)", "Hash (if used)", "Group ID (if duplicate)"])
                group_counter = 1
                for group in duplicate_groups:
                    for p in group:
                        hash_val = ''
                        if use_hash:
                            with open(p, 'rb') as f_hash:
                                hash_val = hashlib.sha256(f_hash.read()).hexdigest()
                        writer.writerow([p, os.path.getsize(p), hash_val, group_counter])
                    group_counter += 1

                if not detect_dups:
                    for p in found_files:
                        writer.writerow([p, os.path.getsize(p), '', ''])

            self.result_area.AppendText(f"\nResults exported to: {csv_file}\n")

        elif output_format == "html":
            html_file = os.path.join(directory, "file_search_results.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write("<html><body><h2>File Search Results</h2><table border='1'>")
                f.write("<tr><th>File Path</th><th>Size (Bytes)</th><th>Hash (if used)</th><th>Group ID (if duplicate)</th></tr>")
                group_counter = 1
                for group in duplicate_groups:
                    for p in group:
                        hash_val = ''
                        if use_hash:
                            with open(p, 'rb') as f_hash:
                                hash_val = hashlib.sha256(f_hash.read()).hexdigest()
                        f.write(f"<tr><td>{p}</td><td>{os.path.getsize(p)}</td><td>{hash_val}</td><td>{group_counter}</td></tr>")
                    group_counter += 1

                if not detect_dups:
                    for p in found_files:
                        f.write(f"<tr><td>{p}</td><td>{os.path.getsize(p)}</td><td></td><td></td></tr>")

                f.write("</table></body></html>")

            self.result_area.AppendText(f"\nResults exported to: {html_file}\n")

        self.progress.SetValue(100)

if __name__ == '__main__':
    app = wx.App()
    FileSearchApp(None).Show()
    app.MainLoop()
