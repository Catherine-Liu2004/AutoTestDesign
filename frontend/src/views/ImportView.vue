<template>
  <div>
    <div class="page-header">
      <h2>Import Requirements</h2>
      <p>Paste functional requirements (one per paragraph) or upload a CSV/TXT file.</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon color="#3b82f6"><EditPen /></el-icon>
              <span style="font-weight:600">Requirement Input</span>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item label="Source Type">
              <el-radio-group v-model="form.source_type">
                <el-radio-button value="direct">Direct Text</el-radio-button>
                <el-radio-button value="csv">CSV</el-radio-button>
                <el-radio-button value="txt">TXT File</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="Content">
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="10"
                placeholder="Example:&#10;Users can register with username, email and password.&#10;&#10;The system must validate email format during registration.&#10;&#10;Passwords must be at least 8 characters long."
                style="font-family:monospace;font-size:13px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleImport" :loading="loading" :icon="Upload">
                Import
              </el-button>
              <el-button @click="handleParseBatch" :loading="parsing" :icon="MagicStick" style="margin-left:8px">
                Parse All with AI
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon color="#10b981"><InfoFilled /></el-icon>
              <span style="font-weight:600">Format Guide</span>
            </div>
          </template>
          <div style="font-size:13px;color:#475569;line-height:1.8">
            <p style="margin:0 0 8px 0"><strong>Direct Text</strong></p>
            <p style="margin:0 0 12px 0;color:#64748b">Separate multiple requirements with a blank line. Each paragraph becomes one requirement.</p>
            <p style="margin:0 0 8px 0"><strong>CSV</strong></p>
            <p style="margin:0 0 12px 0;color:#64748b">Columns named <code>requirement</code>, <code>description</code>, or <code>text</code> are auto-detected.</p>
            <p style="margin:0 0 8px 0"><strong>Workflow</strong></p>
            <ol style="margin:0;padding-left:16px;color:#64748b">
              <li>Import requirements</li>
              <li>Click "Parse All with AI" to extract structure</li>
              <li>Go to Requirements → Analyze Risk</li>
              <li>Go to Test Cases → Generate</li>
            </ol>
          </div>
        </el-card>

        <!-- Import result summary -->
        <el-card v-if="imported.length" style="margin-top:16px">
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon color="#10b981"><CircleCheck /></el-icon>
              <span style="font-weight:600">Imported {{ imported.length }} requirement(s)</span>
            </div>
          </template>
          <div v-for="r in imported" :key="r.id" style="padding:4px 0;border-bottom:1px solid #f1f5f9;font-size:13px">
            <el-text type="info" size="small" style="margin-right:8px">{{ r.id.slice(0,8) }}</el-text>
            <span style="color:#334155">{{ r.raw_text.slice(0, 70) }}{{ r.raw_text.length > 70 ? '…' : '' }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, MagicStick, InfoFilled, CircleCheck, EditPen } from '@element-plus/icons-vue'
import { importRequirements, parseBatch } from '../api/index.js'

const form = ref({ source_type: 'direct', content: '' })
const loading = ref(false)
const parsing = ref(false)
const imported = ref([])

async function handleImport() {
  if (!form.value.content.trim()) return ElMessage.warning('Content is empty')
  loading.value = true
  try {
    const { data } = await importRequirements(form.value)
    imported.value = data
    ElMessage.success(`Imported ${data.length} requirement(s)`)
    form.value.content = ''
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function handleParseBatch() {
  parsing.value = true
  try {
    const { data } = await parseBatch()
    ElMessage.success(`Parsed ${data.length} requirement(s)`)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    parsing.value = false
  }
}
</script>
