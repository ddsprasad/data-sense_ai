import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RagFilesComponent } from './rag-files.component';

describe('RagFilesComponent', () => {
  let component: RagFilesComponent;
  let fixture: ComponentFixture<RagFilesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RagFilesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(RagFilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
