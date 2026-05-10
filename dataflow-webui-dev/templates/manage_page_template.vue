<template>
    <!-- DataFlow WebUI 管理页面模板 -->
    <!-- 复制此文件到 frontend/src/views/manage/{feature}/index.vue -->
    <!-- 替换所有 feature/Feature/item/Item 占位符 -->
    <div class="df-feature-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('Feature') }}</p>
            </div>
            <div class="content-block">
                <!-- 新建面板 -->
                <fv-Collapse :theme="theme" v-model="show.add" class="item-card" icon="Add"
                    :title="local('Add Item')" :content="local('Create a new item.')"
                    :disabled-collapse="true" :max-height="'auto'">
                    <template v-slot:extension>
                        <fv-button v-show="show.add" theme="dark" :is-box-shadow="true" :background="gradient"
                            :disabled="!checkAdd() || !lock.add" border-radius="6"
                            style="width: 90px; margin-right: 5px" @click="confirmAdd">
                            {{ local('Confirm') }}
                        </fv-button>
                        <fv-button :theme="show.add ? theme : 'dark'" :is-box-shadow="true"
                            :background="show.add ? '' : gradient" border-radius="6" style="width: 90px"
                            @click="handleAdd">
                            {{ show.add ? local('Cancel') : local('Add') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <div class="item-row column">
                            <p class="item-light-title">{{ local('Name') }}</p>
                            <fv-text-box :theme="theme" v-model="newItem.name" :placeholder="local('Name')"
                                border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                        </div>
                        <hr />
                        <!-- 添加更多字段 -->
                    </template>
                </fv-Collapse>

                <!-- 已有条目列表 -->
                <fv-Collapse :theme="theme" v-for="(item, index) in itemList" :key="item.id"
                    class="item-card" icon="Document" :title="item.name" :max-height="600">
                    <template v-slot:extension>
                        <fv-button theme="dark" background="rgba(191, 95, 95, 1)"
                            foreground="rgba(255, 255, 255, 1)" border-radius="6" :is-box-shadow="true"
                            style="width: 90px" @click="$event.stopPropagation(), delItem(item)">
                            {{ local('Delete') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <hr />
                        <div class="item-row sep">
                            <div class="item-row column no-pad" style="flex: 1">
                                <p class="item-light-title">{{ local('ID') }}</p>
                                <p class="item-std-info">{{ item.id }}</p>
                            </div>
                            <fv-button v-show="item.edit" theme="dark" :is-box-shadow="true"
                                :background="gradient" border-radius="6"
                                :disabled="!checkEdit(item) || !lock.edit"
                                style="width: 90px; margin-right: 5px" @click="confirmEdit(item)">
                                {{ local('Confirm') }}
                            </fv-button>
                            <fv-button :theme="theme" :icon="item.edit ? 'Cancel' : 'Edit'"
                                :is-box-shadow="true" border-radius="6" style="width: 90px"
                                @click="handleEdit(item)">
                                {{ item.edit ? local('Cancel') : local('Edit') }}
                            </fv-button>
                        </div>
                        <hr />
                        <div class="item-row column">
                            <p class="item-light-title">{{ local('Name') }}</p>
                            <fv-text-box :theme="theme" v-model="item.edit_name" border-radius="6"
                                :disabled="!item.edit" :reveal-border="true"
                                :is-box-shadow="item.edit"></fv-text-box>
                        </div>
                        <hr />
                        <!-- 更多字段 -->
                    </template>
                </fv-Collapse>
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
// import { useDataflow } from '@/stores/dataflow'  // 如需全局 store

export default {
    data() {
        return {
            itemList: [],
            newItem: {
                name: ''
            },
            show: {
                add: false
            },
            lock: {
                add: true,
                edit: true,
                delete: true
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient'])
    },
    mounted() {
        this.getItemList()
    },
    methods: {
        async getItemList() {
            let res = await this.$api.feature.list_features().catch((err) => {
                this.$barWarning(err, { status: 'error' })
            })
            if (res && res.code === 200) {
                this.itemList = res.data.map((item) => ({
                    ...item,
                    edit: false,
                    edit_name: item.name
                }))
            }
        },
        handleAdd() {
            this.show.add ^= true
            this.resetAdd()
        },
        resetAdd() {
            this.newItem = { name: '' }
        },
        checkAdd() {
            return !!this.newItem.name
        },
        confirmAdd() {
            if (!this.lock.add || !this.checkAdd()) return
            this.lock.add = false
            this.$api.feature.create_feature(this.newItem)
                .then((res) => {
                    if (res.code === 200) {
                        this.getItemList()
                        this.resetAdd()
                        this.show.add = false
                    } else {
                        this.$barWarning(res.message, { status: 'warning' })
                    }
                    this.lock.add = true
                })
                .catch((err) => {
                    this.$barWarning(err, { status: 'error' })
                    this.lock.add = true
                })
        },
        handleEdit(item) {
            item.edit ^= true
            item.edit_name = item.name
        },
        checkEdit(item) {
            return !!item.edit_name
        },
        confirmEdit(item) {
            if (!this.lock.edit || !this.checkEdit(item)) return
            this.lock.edit = false
            this.$api.feature.update_feature(item.id, { name: item.edit_name })
                .then((res) => {
                    if (res.code === 200) {
                        this.getItemList()
                        item.edit = false
                        this.$barWarning(this.local('Update Success'), { status: 'correct' })
                    } else {
                        this.$barWarning(res.message, { status: 'warning' })
                    }
                    this.lock.edit = true
                })
                .catch((err) => {
                    this.$barWarning(err, { status: 'error' })
                    this.lock.edit = true
                })
        },
        delItem(item) {
            this.$infoBox(this.local('Are you sure to delete?'), {
                status: 'error',
                theme: this.theme,
                confirm: () => {
                    if (!this.lock.delete) return
                    this.lock.delete = false
                    this.$api.feature.delete_feature(item.id)
                        .then((res) => {
                            if (res.code === 200) {
                                this.getItemList()
                                this.$barWarning(this.local('Delete Success'), { status: 'correct' })
                            } else {
                                this.$barWarning(res.message, { status: 'warning' })
                            }
                            this.lock.delete = true
                        })
                        .catch((err) => {
                            this.$barWarning(err, { status: 'error' })
                            this.lock.delete = true
                        })
                }
            })
        }
    }
}
</script>

<style lang="scss">
.df-feature-container {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: rgba(241, 241, 241, 1);
    display: flex;
    justify-content: center;

    &.dark {
        background: rgba(36, 36, 36, 1);
        .major-container .title-block .main-title { color: whitesmoke; }
    }

    .major-container {
        width: 100%;
        max-width: 1200px;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;

        .title-block {
            position: absolute;
            width: 100%;
            padding: 15px;
            padding-top: 30px;
            z-index: 1;
            backdrop-filter: blur(20px);

            .main-title {
                font-size: 28px;
                font-weight: 400;
                color: rgba(26, 26, 26, 1);
            }
        }

        .content-block {
            position: relative;
            width: 100%;
            height: 100%;
            gap: 5px;
            padding: 15px;
            padding-top: 100px;
            display: flex;
            flex-direction: column;
            overflow: overlay;

            .item-card {
                flex-shrink: 0;

                .item-light-title {
                    margin: 5px 0px;
                    font-size: 12px;
                    color: rgba(95, 95, 95, 1);
                    user-select: none;
                }

                .item-std-info {
                    font-size: 13.8px;
                    color: rgba(27, 27, 27, 1);
                    user-select: none;
                }

                .item-row {
                    position: relative;
                    width: 100%;
                    padding: 0px 42px;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;

                    &.no-pad { padding: 0px; }
                    &.sep { justify-content: space-between; }
                    &.column { flex-direction: column; align-items: flex-start; }
                }

                hr {
                    margin: 10px 0px;
                    border: none;
                    border-top: rgba(120, 120, 120, 0.1) solid thin;
                }
            }
        }
    }
}
</style>
