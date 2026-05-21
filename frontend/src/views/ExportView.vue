<template>
  <div>
    <div class="page-header">
      <h2>Export Test Artifacts</h2>
      <p>Download test suites in Excel, JSON, or CSV format.</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon color="#3b82f6"><Download /></el-icon>
              <span style="font-weight:600">Export Options</span>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item>
              <template #label>
                <div style="display:flex;justify-content:space-between;width:100%">
                  <span>Test Suite</span>
                  <el-button link size="small" :icon="Refresh" @click="loadSuites">Refresh</el-button>
                </div>
              </template>
              <el-select
                v-model="form.suite_id"
                placeholder="Select a test suite"
                style="width:100%"
                v-loading="loadingSuites"
              >
                <el-option
                  v-for="s in suites"
                  :key="s.id"
                  :value="s.id"
                  :label="`${s.name}  (${s.tc_count} cases · ${formatDate(s.created_at)})`"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="Export Format">
              <el-radio-group v-model="form.format">
                <el-radio-button value="excel">
                  <el-icon style="margin-right:4px"><Grid /></el-icon> Excel (.xlsx)
                </el-radio-button>
                <el-radio-button value="json">
                  <el-icon style="margin-right:4px"><Document /></el-icon> JSON
                </el-radio-button>
                <el-radio-button value="csv">
                  <el-icon style="margin-right:4px"><List /></el-icon> CSV
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="Include Sheets">
              <el-checkbox-group v-model="form.include">
                <el-checkbox value="test_cases">Test Cases</el-checkbox>
                <el-checkbox value="risk_report">Risk Report</el-checkbox>
                <el-checkbox value="traceability_matrix">Traceability Matrix</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <el-button
                type="success"
                :icon="Download"
                size="large"
                @click="handleExport"
                :loading="exporting"
                :disabled="!form.suite_id"
                style="width:100%"
              >
                Download Export
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card v-if="form.suite_id && selectedSuite">
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon color="#10b981"><InfoFilled /></el-icon>
              <span style="font-weight:600">Suite Info</span>
            </div>
          </template>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item label="Name">{{ selectedSuite.name }}</el-descriptions-item>
            <el-descriptions-item label="Test Cases">
              <el-badge :value="selectedSuite.tc_count" type="primary" />
            </el-descriptions-item>
            <el-descriptions-item label="Techniques">
              <el-tag
                v-for="t in (selectedSuite.techniques || [])"
                :key="t"
                size="small"
                style="margin:2px"
              >{{ t.replace('_', ' ') }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Created">{{ formatDate(selectedSuite.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="Suite ID">
              <el-text type="info" size="small" style="font-family:monospace">{{ selectedSuite.id }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card v-else>
          <el-empty description="Select a test suite to see details" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Refresh, Grid, Document, List, InfoFilled } from '@element-plus/icons-vue'
import { exportArtifacts, listTestSuites } from '../api/index.js'

const suites = ref([])
const loadingSuites = ref(false)
const form = ref({
  suite_id: '',
  format: 'excel',
  include: ['test_cases', 'risk_report', 'traceability_matrix'],
})
const exporting = ref(false)

const selectedSuite = computed(() => suites.value.find(s => s.id === form.value.suite_id) || null)

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : ''
}

async function loadSuites() {
  loadingSuites.value = true
  try {
    const { data } = await listTestSuites()
    suites.value = data
    if (data.length && !form.value.suite_id) {
      form.value.suite_id = data[0].id
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loadingSuites.value = false
  }
}

async function handleExport() {
  if (!form.value.suite_id) return ElMessage.warning('Select a test suite')
  exporting.value = true
  try {
    const { data } = await exportArtifacts(form.value)
    const ext = form.value.format === 'excel' ? 'xlsx' : form.value.format
    const url = URL.createObjectURL(new Blob([data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `export_${form.value.suite_id.slice(0,8)}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Export downloaded')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    exporting.value = false
  }
}

onMounted(loadSuites)
</script>

