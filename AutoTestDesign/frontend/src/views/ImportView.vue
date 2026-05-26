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
              <el-radio-group v-model="form.source_type" @change="handleSourceTypeChange">
                <el-radio-button value="direct">Direct Text</el-radio-button>
                <el-radio-button value="csv">CSV</el-radio-button>
                <el-radio-button value="txt">TXT File</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- Direct text input -->
            <el-form-item v-if="form.source_type === 'direct'" label="Content">
              <el-input
                v-model="form.content"
                type="textarea"
                :rows="10"
                placeholder="Example:&#10;Users can register with username, email and password.&#10;&#10;The system must validate email format during registration.&#10;&#10;Passwords must be at least 8 characters long."
                style="font-family:monospace;font-size:13px"
              />
            </el-form-item>

            <!-- File upload for CSV / TXT -->
            <el-form-item v-else :label="form.source_type === 'csv' ? 'Upload CSV File' : 'Upload TXT File'">
              <el-upload
                drag
                :auto-upload="false"
                :multiple="false"
                :accept="form.source_type === 'csv' ? '.csv' : '.txt'"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :file-list="fileList"
                :limit="1"
                :on-exceed="() => ElMessage.warning('Only one file is allowed')"
                style="width:100%"
              >
                <el-icon style="font-size:48px;color:#c0c4cc"><UploadFilled /></el-icon>
                <div style="margin-top:8px;font-size:14px;color:#606266">
                  Drop file here or <em style="color:#409eff">click to select</em>
                </div>
                <template #tip>
                  <div style="font-size:12px;color:#909399;margin-top:4px">
                    {{ form.source_type === 'csv' ? 'Only .csv files are accepted' : 'Only .txt files are accepted' }}
                  </div>
                </template>
              </el-upload>
              <!-- File content preview -->
              <el-input
                v-if="form.content"
                v-model="form.content"
                type="textarea"
                :rows="6"
                style="margin-top:12px;font-family:monospace;font-size:12px"
                placeholder="File content preview..."
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleImport" :loading="loading" :icon="Upload">
                Import
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
              <li>Import requirements here</li>
              <li>Go to <strong>Requirements</strong> → click "Parse All (AI)"</li>
              <li>Click "Analyze Risk (AI)"</li>
              <li>Go to <strong>Test Cases</strong> → Generate</li>
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
import { Upload, InfoFilled, CircleCheck, EditPen, UploadFilled } from '@element-plus/icons-vue'
import { importRequirements } from '../api/index.js'

const form = ref({ source_type: 'direct', content: '' })
const loading = ref(false)
const imported = ref([])
const fileList = ref([])

function handleSourceTypeChange() {
  form.value.content = ''
  fileList.value = []
}

function handleFileChange(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.content = e.target.result
  }
  reader.readAsText(file.raw, 'UTF-8')
}

function handleFileRemove() {
  form.value.content = ''
  fileList.value = []
}

async function handleImport() {
  if (!form.value.content.trim()) return ElMessage.warning('Content is empty')
  loading.value = true
  try {
    const { data } = await importRequirements(form.value)
    imported.value = data
    ElMessage.success(`Imported ${data.length} requirement(s)`)
    form.value.content = ''
    fileList.value = []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

</script>
