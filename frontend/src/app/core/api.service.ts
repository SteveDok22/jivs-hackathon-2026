import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { delay } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { CANNED_EVAL, findCanned } from './canned';
import { AgentAnswer, EvalReport } from './models';

// Single gateway to the backend. Every component talks to the API through this
// service. In demo mode (the public Vercel build) there is no backend: the
// service returns captured real responses so the site stays live and free.
// In dev it calls the FastAPI server through the proxy.
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBase;

  readonly demoMode = environment.demoMode;
  readonly repoUrl = environment.repoUrl;

  ask(question: string, directory = 'data/synthetic'): Observable<AgentAnswer> {
    if (this.demoMode) {
      const canned = findCanned(question);
      if (canned) {
        // Small delay so the live "scanning" animation still plays.
        return of(canned).pipe(delay(900));
      }
      // Unknown question in demo mode: signal the console to show the
      // "run locally" note rather than a fake answer.
      return throwError(() => ({ demo: true })).pipe(delay(300));
    }
    return this.http.post<AgentAnswer>(`${this.base}/agent/ask`, { question, directory });
  }

  runEval(): Observable<EvalReport> {
    if (this.demoMode) {
      return of(CANNED_EVAL).pipe(delay(1500));
    }
    return this.http.post<EvalReport>(`${this.base}/eval/run`, {});
  }

  report(): Observable<EvalReport> {
    if (this.demoMode) {
      return of(CANNED_EVAL);
    }
    return this.http.get<EvalReport>(`${this.base}/eval/report`);
  }
}
