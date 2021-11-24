import { HttpClient } from "@angular/common/http";
import { Component, ViewChild, ElementRef } from "@angular/core";
import { MatButtonToggleChange } from "@angular/material/button-toggle";

@Component({
  selector: "app-root",
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.scss"],
})
export class AppComponent {
  @ViewChild("fileDropRef", { static: false }) fileDropEl: ElementRef;
  files: any[] = [];
  operation = "encode";
  steganographyMethod = "lsb";
  messagePlaceholderValue = "Message to be encoded";
  showMessageBox = true;
  isReadOnly = false;
  message = "";

  constructor(private http: HttpClient) {}

  /**
   * on file drop handler
   */
  onFileDropped($event) {
    this.prepareFilesList($event);
  }

  /**
   * handle file from browsing
   */
  fileBrowseHandler(files) {
    this.prepareFilesList(files);
  }

  /**
   * Delete file from files list
   * @param index (File index)
   */
  deleteFile(index: number) {
    this.files.splice(index, 1);
  }

  /**
   * Convert Files list to normal array list
   * @param files (Files List)
   */
  prepareFilesList(files: Array<any>) {
    for (const item of files) {
      this.files = [];
      this.files.push(item);
    }
    this.fileDropEl.nativeElement.value = "";
    // this.uploadFilesSimulator(0);
  }

  /**
   * format bytes
   * @param bytes (File size in bytes)
   * @param decimals (Decimals point)
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) {
      return "0 Bytes";
    }
    const k = 1024;
    const dm = decimals <= 0 ? 0 : decimals;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }

  onOperationChange(change: MatButtonToggleChange) {
    this.operation = change.value;
    if (this.operation == 'encode') {
      this.messagePlaceholderValue = "Message to be encoded";
      this.showMessageBox = true;
      this.isReadOnly = false;
    } else {
      this.messagePlaceholderValue = "Decoded message";
      this.showMessageBox = false;
      this.isReadOnly = true;
    }
  }

  onSteganographyMethodChange(change: MatButtonToggleChange) {
    this.steganographyMethod = change.value;
  }

  onSubmit() {
    console.log('test')
  }

}
