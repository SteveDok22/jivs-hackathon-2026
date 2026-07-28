import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AgentAnswer, EvalReport } from './models';

// Single gateway to the backend. Every component talks to the API through
// this service, never via HttpClient directly — one place to change the base
// URL when we deploy to AWS.
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBase;

  ask(question: string, directory = 'data/synthetic'): Observable<AgentAnswer> {
    return this.http.post<AgentAnswer>(`${this.base}/agent/ask`, { question, directory });
  }

  runEval(): Observable<EvalReport> {
    return this.http.post<EvalReport>(`${this.base}/eval/run`, {});
  }

  report(): Observable<EvalReport> {
    return this.http.get<EvalReport>(`${this.base}/eval/report`);
  }
}
