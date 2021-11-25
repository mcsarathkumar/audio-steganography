import { HttpClient, HttpErrorResponse, HttpEventType, HttpRequest, HttpResponse } from "@angular/common/http";
import { Component, ViewChild, ElementRef } from "@angular/core";
import { MatButtonToggleChange } from "@angular/material/button-toggle";
import { environment } from "src/environments/environment";
import { saveAs } from 'file-saver';
import { MatSnackBar } from "@angular/material/snack-bar";

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
  showProgress = false;
  progressMode = 'determinate';
  progressValue = 0;

  constructor(private http: HttpClient, private snackBar: MatSnackBar) { }

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
    const formData = new FormData();
    const fileName = this.files[0].name;
    formData.append("file", this.files[0], fileName);
    formData.append("operation", this.operation);
    formData.append("method", this.steganographyMethod);
    const options = {};
    if (this.operation == 'encode') {
      formData.append("message", this.message);
      options['responseType'] = 'blob';
    }
    options['reportProgress'] = true;
    const req = new HttpRequest('POST', environment.apiUrl + 'process', formData, options);
    this.showProgress = true;
    this.progressMode = 'determinate';
    this.http.request(req).subscribe(
      {
        next: (event: any) => {
          if (event.type === HttpEventType.UploadProgress) {
            this.progressValue = Math.round(100 * event.loaded / event.total);
            if (this.progressValue == 100) {
              this.progressMode = 'indeterminate';
            }
          } else if (event instanceof HttpResponse) {
            const response = event;
            if (this.operation == 'encode') {
              const fileNameLower = fileName.toLowerCase();
              const fileNamePos = fileNameLower.lastIndexOf('.wav');
              saveAs(response.body as Blob, this.files[0].name.slice(0, fileNamePos) + '_' + this.steganographyMethod + '_encoded' + fileName.slice(fileNamePos));
            } else {
              this.isReadOnly = true;
              this.showMessageBox = true;
              this.messagePlaceholderValue = "Decoded message";
              this.message = response.body['message'];
            }
            this.showProgress = false;
          }
        },
        error: (err) => {
          if (err instanceof HttpErrorResponse) {
            if (this.operation == "encode") {
              err.error.text().then(error => {
                const errorObj = JSON.parse(error);
                this.openSnackBar(errorObj.message);
              });
            } else {
              this.openSnackBar(err.error.message);
            }
            this.showProgress = false;
          }
        }
      });
  }

  resetForm() {
    this.files = [];
    this.operation = "encode";
    this.steganographyMethod = "lsb";
    this.messagePlaceholderValue = "Message to be encoded";
    this.showMessageBox = true;
    this.isReadOnly = false;
    this.message = "";
  }

  openSnackBar(message: string) {
    this.snackBar.open(message, 'Ok', {
      duration: 3000
    });
  }
}
