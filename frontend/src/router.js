import { createRouter, createWebHistory } from 'vue-router'
import ImportView from './views/ImportView.vue'
import RequirementsView from './views/RequirementsView.vue'
import TestCasesView from './views/TestCasesView.vue'
import ExportView from './views/ExportView.vue'

const routes = [
  { path: '/', component: ImportView },
  { path: '/requirements', component: RequirementsView },
  { path: '/testcases', component: TestCasesView },
  { path: '/export', component: ExportView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
