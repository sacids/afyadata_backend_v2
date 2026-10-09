function webFormFill(initialPage, pageCount) {
    return {
        currentPage: initialPage || 0,
        pageCount: pageCount || 0,
        values: {},
        errors: {},

        init() {
            this.refreshValues();
            this.syncAllFieldStates();
            this.$refs.form.addEventListener('input', (event) => {
                this.refreshValues();
                this.validateFieldByInput(event.target);
                this.syncAllFieldStates();
            });
            this.$refs.form.addEventListener('change', (event) => {
                this.refreshValues();
                this.validateFieldByInput(event.target);
                this.syncAllFieldStates();
            });
        },

        refreshValues() {
            const values = {};
            const formData = new FormData(this.$refs.form);
            for (const [key, value] of formData.entries()) {
                if (Object.prototype.hasOwnProperty.call(values, key)) {
                    if (!Array.isArray(values[key])) values[key] = [values[key]];
                    values[key].push(value);
                } else {
                    values[key] = value;
                }
            }
            this.values = values;
        },

        syncAllFieldStates() {
            this.$refs.form.querySelectorAll('[data-field-wrapper]').forEach((wrapper) => {
                this.syncFieldState(wrapper, wrapper.dataset.relevant || '');
            });
            this.ensureVisiblePage();
        },

        syncFieldState(wrapper, expression) {
            const relevant = this.isRelevant(expression || '');
            wrapper.querySelectorAll('input, select, textarea').forEach((input) => {
                if (input.dataset.originalDisabled === undefined) {
                    input.dataset.originalDisabled = input.disabled ? 'true' : 'false';
                }
                input.disabled = !relevant || input.dataset.originalDisabled === 'true';
            });
            if (!relevant) {
                this.clearFieldError(wrapper.dataset.fieldName);
            }
        },

        ensureVisiblePage() {
            if (this.pageIsRelevant(this.currentPage)) return;
            for (let index = 0; index < this.pageCount; index += 1) {
                if (this.pageIsRelevant(index)) {
                    this.currentPage = index;
                    return;
                }
            }
        },

        goNext() {
            if (!this.validatePage(this.currentPage, true)) return;
            let nextPage = this.currentPage + 1;
            while (nextPage < this.pageCount && !this.pageIsRelevant(nextPage)) {
                nextPage += 1;
            }
            this.currentPage = Math.min(nextPage, this.pageCount - 1);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        validateCurrentPage() {
            return this.validatePage(this.currentPage, true);
        },

        validatePage(pageIndex, focusFirstError = false) {
            this.refreshValues();
            let firstInvalid = null;
            const fields = this.$refs.form.querySelectorAll(`[data-page="${pageIndex}"][data-field-wrapper]`);
            fields.forEach((wrapper) => {
                if (!this.wrapperIsActive(wrapper)) return;
                const message = this.validateWrapper(wrapper);
                if (message) {
                    this.setFieldError(wrapper.dataset.fieldName, message);
                    if (!firstInvalid) firstInvalid = wrapper;
                } else {
                    this.clearFieldError(wrapper.dataset.fieldName);
                }
            });

            if (firstInvalid && focusFirstError) {
                const firstInput = firstInvalid.querySelector('input:not([disabled]), select:not([disabled]), textarea:not([disabled])');
                if (firstInput) firstInput.focus();
            }
            return !firstInvalid;
        },

        validateFieldByInput(input) {
            const wrapper = input.closest('[data-field-wrapper]');
            if (!wrapper || !this.wrapperIsActive(wrapper)) return;
            const message = this.validateWrapper(wrapper);
            if (message) {
                this.setFieldError(wrapper.dataset.fieldName, message);
            } else {
                this.clearFieldError(wrapper.dataset.fieldName);
            }
        },

        validateWrapper(wrapper) {
            const fieldName = wrapper.dataset.fieldName;
            const label = wrapper.dataset.label || fieldName;
            const fieldType = wrapper.dataset.fieldType || 'text';
            const value = this.getFieldValue(wrapper);

            if (wrapper.dataset.required === 'true' && !this.hasFieldValue(value)) {
                return `${label} is required.`;
            }

            if (this.hasFieldValue(value) && ['integer', 'int'].includes(fieldType)) {
                if (!/^-?\d+$/.test(String(value).trim())) return `${label} must be a whole number.`;
            }

            if (this.hasFieldValue(value) && ['decimal', 'float'].includes(fieldType)) {
                if (Number.isNaN(Number(value))) return `${label} must be a valid number.`;
            }

            const constraint = wrapper.dataset.constraint || '';
            if (this.hasFieldValue(value) && constraint && !this.evaluateExpression(constraint, value)) {
                return wrapper.dataset.constraintMessage || 'This value is not valid.';
            }

            return '';
        },

        getFieldValue(wrapper) {
            const fieldName = wrapper.dataset.fieldName;
            const inputs = Array.from(wrapper.querySelectorAll(`[name="${CSS.escape(fieldName)}"]`))
                .filter((input) => !input.disabled);
            const fileInput = inputs.find((input) => input.type === 'file');
            if (fileInput) return fileInput.files ? Array.from(fileInput.files) : [];

            const selectedInputs = inputs.filter((input) => input.type === 'checkbox' || input.type === 'radio');
            if (selectedInputs.length) {
                return selectedInputs.filter((input) => input.checked).map((input) => input.value);
            }

            return inputs[0] ? inputs[0].value : '';
        },

        hasFieldValue(value) {
            if (Array.isArray(value)) return value.length > 0;
            return String(value || '').trim() !== '';
        },

        wrapperIsActive(wrapper) {
            return this.isRelevant(wrapper.dataset.relevant || '');
        },

        setFieldError(fieldName, message) {
            if (!fieldName) return;
            this.errors = { ...this.errors, [fieldName]: message };
        },

        clearFieldError(fieldName) {
            if (!fieldName || !this.errors[fieldName]) return;
            const errors = { ...this.errors };
            delete errors[fieldName];
            this.errors = errors;
        },

        fieldError(fieldName) {
            return this.errors[fieldName] || '';
        },

        submitForm(event) {
            this.syncAllFieldStates();
            this.refreshValues();
            for (let index = 0; index < this.pageCount; index += 1) {
                if (!this.pageIsRelevant(index)) continue;
                if (!this.validatePage(index, false)) {
                    event.preventDefault();
                    this.currentPage = index;
                    this.$nextTick(() => {
                        const firstErrorWrapper = Array.from(this.$refs.form.querySelectorAll(`[data-page="${index}"][data-field-wrapper]`))
                            .find((wrapper) => this.errors[wrapper.dataset.fieldName]);
                        const firstInput = firstErrorWrapper ? firstErrorWrapper.querySelector('input:not([disabled]), select:not([disabled]), textarea:not([disabled])') : null;
                        if (firstInput) firstInput.focus();
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                    return false;
                }
            }
            this.syncAllFieldStates();
            return true;
        },

        isRelevant(expression) {
            if (!expression) return true;
            return this.evaluateExpression(expression, '');
        },

        evaluateExpression(expression, currentValue = '') {
            let expr = String(expression || '').trim();
            if (!expr) return true;
            expr = this.stripWrappingParentheses(expr);

            const notExpression = expr.match(/^not\s*\((.*)\)$/i);
            if (notExpression) {
                return !this.evaluateExpression(notExpression[1], currentValue);
            }

            const selected = expr.match(/^selected\(\s*\$\{([^}]+)\}\s*,\s*['"]([^'"]+)['"]\s*\)$/i);
            if (selected) {
                const values = this.asArray(this.values[selected[1]]);
                return values.map(String).includes(selected[2]);
            }

            const regex = expr.match(/^regex\(\s*\.\s*,\s*['"]([^'"]+)['"]\s*\)$/i);
            if (regex) {
                try {
                    return new RegExp(regex[1]).test(String(currentValue || ''));
                } catch (error) {
                    return true;
                }
            }

            const parts = this.splitLogicalExpression(expr);
            if (parts.length > 1) {
                let result = this.evaluateExpression(parts[0], currentValue);
                for (let i = 1; i < parts.length; i += 2) {
                    const op = parts[i].toLowerCase();
                    const next = this.evaluateExpression(parts[i + 1], currentValue);
                    result = op === 'and' ? (result && next) : (result || next);
                }
                return result;
            }

            const comparison = expr.match(/^(\.|\$\{[^}]+\})\s*(=|!=|>=|<=|>|<)\s*(.+)$/);
            if (!comparison) return true;

            const left = this.resolveOperand(comparison[1], currentValue);
            const right = this.resolveOperand(comparison[3], currentValue);
            return this.compare(left, comparison[2], right);
        },

        resolveOperand(value, currentValue = '') {
            const trimmed = String(value || '').trim();
            if (trimmed === '.') return currentValue;
            if (trimmed.startsWith('${') && trimmed.endsWith('}')) {
                return this.values[trimmed.slice(2, -1)] || '';
            }
            if ((trimmed.startsWith("'") && trimmed.endsWith("'")) || (trimmed.startsWith('"') && trimmed.endsWith('"'))) {
                return trimmed.slice(1, -1);
            }
            const numberValue = Number(trimmed);
            return Number.isNaN(numberValue) ? trimmed : numberValue;
        },

        splitLogicalExpression(expression) {
            const parts = [];
            let depth = 0;
            let quote = '';
            let buffer = '';

            for (let index = 0; index < String(expression || '').length; index += 1) {
                const char = expression[index];

                if (quote) {
                    buffer += char;
                    if (char === quote) quote = '';
                    continue;
                }

                if (char === "'" || char === '"') {
                    quote = char;
                    buffer += char;
                    continue;
                }

                if (char === '(') {
                    depth += 1;
                    buffer += char;
                    continue;
                }

                if (char === ')') {
                    depth = Math.max(depth - 1, 0);
                    buffer += char;
                    continue;
                }

                if (depth === 0) {
                    const remaining = expression.slice(index);
                    const logical = remaining.match(/^\s+(and|or)\s+/i);
                    if (logical) {
                        parts.push(buffer.trim(), logical[1].toLowerCase());
                        buffer = '';
                        index += logical[0].length - 1;
                        continue;
                    }
                }

                buffer += char;
            }

            if (buffer.trim()) parts.push(buffer.trim());
            return parts.length > 1 ? parts : [expression];
        },

        compare(left, operator, right) {
            const leftNumber = Number(left);
            const rightNumber = Number(right);
            const useNumber = !Number.isNaN(leftNumber) && !Number.isNaN(rightNumber);
            const a = useNumber ? leftNumber : String(left);
            const b = useNumber ? rightNumber : String(right);
            if (operator === '=') return a === b;
            if (operator === '!=') return a !== b;
            if (operator === '>') return a > b;
            if (operator === '<') return a < b;
            if (operator === '>=') return a >= b;
            if (operator === '<=') return a <= b;
            return true;
        },

        stripWrappingParentheses(expression) {
            let expr = String(expression || '').trim();
            while (expr.startsWith('(') && expr.endsWith(')')) {
                let depth = 0;
                let wraps = true;
                for (let i = 0; i < expr.length; i += 1) {
                    if (expr[i] === '(') depth += 1;
                    if (expr[i] === ')') {
                        depth -= 1;
                        if (depth === 0 && i !== expr.length - 1) {
                            wraps = false;
                            break;
                        }
                    }
                }
                if (!wraps) break;
                expr = expr.slice(1, -1).trim();
            }
            return expr;
        },

        goPrevious() {
            let nextPage = this.currentPage - 1;
            while (nextPage >= 0 && !this.pageIsRelevant(nextPage)) {
                nextPage -= 1;
            }
            this.currentPage = Math.max(nextPage, 0);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        pageIsRelevant(pageIndex) {
            const section = this.$refs.form.querySelector(`[data-page-section="${pageIndex}"]`);
            if (!section) return false;
            return this.isRelevant(section.dataset.pageRelevant || '');
        },

        asArray(value) {
            if (value === undefined || value === null || value === '') return [];
            return Array.isArray(value) ? value : [value];
        },
    };
}
