import { Clipboard } from '@angular/cdk/clipboard';
import { Injectable } from '@angular/core';
import { MatIconRegistry } from "@angular/material/icon";
import { DomSanitizer } from "@angular/platform-browser";
import { BehaviorSubject, Subject } from 'rxjs';
import { v4 as uuidv4 } from 'uuid';
import {
  MatSnackBar,
  MatSnackBarHorizontalPosition,
  MatSnackBarVerticalPosition,
} from '@angular/material/snack-bar';
import { duration } from 'moment';

@Injectable({
  providedIn: 'root'
})

export class UtilService {
  librarySubject = new Subject<boolean | string>();
  hightLight = new BehaviorSubject<string>('');
  constructor(
    private matIconRegistry: MatIconRegistry,
    private domSanitizer: DomSanitizer,
    private clipboard: Clipboard,
    private _snackBar: MatSnackBar
  ) {
  }

  private dropdownChangeSource = new Subject<void>();
  dropdownChange$ = this.dropdownChangeSource.asObservable();

  // Method to call when dropdown changes
  notifyDropdownChange() {
    this.dropdownChangeSource.next();
  }

  /**
   *
   * @param iconName name of the icon to add in <mat-icon>{iconName}</mat-icon>
   * @param iconPath icon path
   */
  matICONGenerator(iconName: string, iconPath: string) {
    this.matIconRegistry.addSvgIcon(
      iconName,
      this.domSanitizer.bypassSecurityTrustResourceUrl(iconPath)
    );
  }

  matIconListGenerate() {
    this.matICONGenerator('hidemenu', '../assets/icons/sidemenu/hidemenu.svg');
    this.matICONGenerator('library', '../assets/icons/sidemenu/library.svg');
    this.matICONGenerator('ai-plus', '../assets/icons/sidemenu/plus.svg');
    this.matICONGenerator('ai-rag', '../assets/icons/sidemenu/rag.svg');
    this.matICONGenerator('aisend', '../assets/icons/questions/send.svg');
    this.matICONGenerator('datacellcenter', '../assets/icons/questions/datacellcenter.svg');
    this.matICONGenerator('revenue', '../assets/icons/questions/revenue.svg');
    this.matICONGenerator('ai-answer', '../assets/icons/answer/answer.svg');
    this.matICONGenerator('ai-copy', '../assets/icons/answer/copy.svg');
    this.matICONGenerator('ai-edit', '../assets/icons/answer/edit.svg');
    this.matICONGenerator('ai-like', '../assets/icons/answer/like.svg');
    this.matICONGenerator('ai-question', '../assets/icons/answer/question.svg');
    this.matICONGenerator('ai-share', '../assets/icons/answer/share.svg');
    this.matICONGenerator('ai-codecopy', '../assets/icons/answer/codecopy.svg');
    this.matICONGenerator('ai-related', '../assets/icons/answer/related.svg');
    this.matICONGenerator('ai-settings', '../assets/icons/sidemenu/settings.svg');
    this.matICONGenerator('ai-questionedit', '../assets/icons/answer/editQuestion.svg');
    this.matICONGenerator('ai-delete', '../assets/icons/answer/delete.svg');
    this.matICONGenerator('ai-plusIcon', '../assets/icons/sidemenu/plusIcon.svg');
    this.matICONGenerator('ai-chatIcon', '../assets/icons/sidemenu/newchaticon.svg');
    this.matICONGenerator('ai-tag', '../assets/icons/answer/tag.svg');
    this.matICONGenerator('ai-uparrow', '../assets/icons/answer/uparrow.svg');
    this.matICONGenerator('ai-relatedInsignts', '../assets/icons/answer/relatedInsignts.svg');
  }

  getUUID() {
    return uuidv4();
  }

  copyToClip(text: string) {
    this.clipboard.copy(text);
  }
  /**
   * 
   * @param text display Text
   * @param cls 'success', 'danger', 'info'
   */
  showSnackBar(text: string, cls: string = 'success') {
    this._snackBar.open(text, '', {
      duration: 1500,
      panelClass: [cls]
    });
  }

}
