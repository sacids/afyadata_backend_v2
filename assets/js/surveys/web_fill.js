function webFormFill(initialPage, pageCount) {
    return {
        currentPage: initialPage || 0,
        pageCount: pageCount || 0,
        values: {},
        errors: {},
        calculations: [],
        calculationErrors: {},
        choiceFilters: [],
        choiceFilterErrors: {},

        init() {
            this.errors = JSON.parse(document.getElementById('web-form-errors')?.textContent || '{}');
            this.calculations = JSON.parse(document.getElementById('web-form-calculations')?.textContent || '[]');
            this.choiceFilters = JSON.parse(document.getElementById('web-form-choice-filters')?.textContent || '[]');
            this.refreshValues();
            this.syncChoiceFilters();
            this.syncAllFieldStates();
            this.$refs.form.addEventListener('input', event => this.handleFormInput(event));
            this.$refs.form.addEventListener('change', event => this.handleFormInput(event));
        },

        handleFormInput(event) {
            const previous = { ...this.values };
            this.refreshValues();
            this.syncChoiceFilters(previous);
            this.syncAllFieldStates();
            this.validateFieldByInput(event.target);
        },

        choiceValueSignature(value) {
            return JSON.stringify(Array.isArray(value) ? value.map(String).sort() : String(value ?? ''));
        },

        syncChoiceFilters(previous = null) {
            if (!this.choiceFilters.length) return;
            const changed = new Set();
            const reset = new Set();
            const recordChanges = before => {
                Object.keys({ ...before, ...this.values }).forEach(name => {
                    if (this.choiceValueSignature(before[name]) !== this.choiceValueSignature(this.values[name])) changed.add(name);
                });
            };
            if (previous) recordChanges(previous);

            // Walk the cascade to a stable state, including filters which depend
            // on calculated values changed by an upstream selection reset.
            for (let pass = 0; pass < this.choiceFilters.length + this.calculations.length + 1; pass += 1) {
                const before = { ...this.values };
                const changedCount = changed.size;
                const errors = {};
                let cleared = false;
                this.choiceFilters.forEach(filter => {
                    let selectionCleared = false;
                    const controls = Array.from(this.$refs.form.querySelectorAll(`[name="${CSS.escape(filter.name)}"]`));
                    const resetSelection = filter.dependencies.some(name => changed.has(name)) && !reset.has(filter.name);
                    if (resetSelection) {
                        reset.add(filter.name);
                        changed.add(filter.name);
                    }
                    let allowed = new Set();
                    try {
                        const values = this.activeCalculationValues();
                        if (!filter.relevant || this.evaluateExpression(filter.relevant, '', values)) {
                            if (filter.error) throw new Error(filter.error);
                            allowed = new Set(filter.options.filter(option => {
                                const result = this.evaluateCalculation(filter.tree, values, option.attributes);
                                return typeof result === 'number' ? Number.isFinite(result) && result !== 0 : Boolean(result);
                            }).map(option => String(option.value)));
                        }
                    } catch (error) {
                        errors[filter.name] = error.message || 'Unable to evaluate this field\'s choice filter.';
                    }
                    controls.forEach(control => {
                        if (control.tagName === 'SELECT') {
                            if (control.dataset.originalDisabled === undefined) control.dataset.originalDisabled = String(control.disabled);
                            const selected = Array.from(control.selectedOptions).map(option => option.value).filter(Boolean);
                            const options = filter.options.filter(option => allowed.has(String(option.value)));
                            const signature = JSON.stringify(options.map(option => [String(option.value), option.label]));
                            if (control.dataset.choiceOptions !== signature || resetSelection) {
                                const fragment = document.createDocumentFragment();
                                if (!control.multiple) fragment.append(new Option(options.length ? 'Select...' : 'No matching options', ''));
                                options.forEach(option => {
                                    const keepSelected = !resetSelection && selected.includes(String(option.value));
                                    fragment.append(new Option(option.label, String(option.value), false, keepSelected));
                                });
                                control.replaceChildren(fragment);
                                control.dataset.choiceOptions = signature;
                            }
                            selectionCleared = selected.some(value => resetSelection || !allowed.has(value));
                            control.dataset.choiceNoOptions = String(options.length === 0);
                            control.disabled = options.length === 0 || control.dataset.originalDisabled === 'true';
                        } else if (control.type === 'checkbox' || control.type === 'radio') {
                            if (control.dataset.originalDisabled === undefined) control.dataset.originalDisabled = String(control.disabled);
                            const available = allowed.has(control.value);
                            control.dataset.choiceFilteredOut = String(!available);
                            control.disabled = !available || control.dataset.originalDisabled === 'true';
                            const label = control.closest('[data-choice-option]');
                            if (label) label.style.display = available ? '' : 'none';
                            if (control.checked && (resetSelection || !available)) {
                                control.checked = false;
                                selectionCleared = true;
                            }
                        }
                    });
                    if (previous && (resetSelection || selectionCleared)) this.clearFieldError(filter.name);
                    cleared = cleared || selectionCleared;
                });
                this.choiceFilterErrors = errors;
                this.refreshValues();
                recordChanges(before);
                if (!cleared && changed.size === changedCount) break;
            }
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
            this.refreshCalculations();
        },

        refreshCalculations() {
            const errors = {};
            this.calculations.forEach(item => { this.values[item.name] = ''; });
            this.calculations.forEach(item => {
                try {
                    const values = this.activeCalculationValues();
                    if (!item.relevant || this.evaluateExpression(item.relevant, '', values)) {
                        if (item.error) throw new Error(item.error);
                        let value = this.evaluateCalculation(item.tree, values);
                        if (typeof value === 'number' && !Number.isFinite(value)) value = '';
                        this.values[item.name] = value;
                    }
                } catch (error) {
                    errors[item.name] = error.message || 'Unable to calculate this field.';
                }
                this.$refs.form.querySelectorAll(`[name="${CSS.escape(item.name)}"]`).forEach(input => {
                    input.value = this.calculationText(this.values[item.name]);
                });
            });
            this.calculationErrors = errors;
        },

        activeCalculationValues() {
            const values = { ...this.values };
            const relevance = {};
            this.$refs.form.querySelectorAll('[data-field-wrapper]').forEach(wrapper => {
                const name = wrapper.dataset.fieldName;
                relevance[name] = wrapper.dataset.relevant || '';
                const inputs = Array.from(wrapper.querySelectorAll(`[name="${CSS.escape(name)}"]`));
                // Conditional controls may still be disabled during the event
                // which makes them relevant again. Read them only for calculations.
                const disabled = inputs.filter(input => input.disabled && input.dataset.originalDisabled === 'false');
                if (!disabled.length) return;
                if (disabled[0].type === 'checkbox' || disabled[0].type === 'radio') {
                    values[name] = disabled.filter(input => input.checked).map(input => input.value);
                } else if (disabled[0].type !== 'file') {
                    values[name] = disabled[0].value;
                }
            });
            this.calculations.forEach(item => { relevance[item.name] = item.relevant || ''; });
            for (let pass = 0; pass < Object.keys(relevance).length; pass += 1) {
                const inactive = Object.keys(relevance).filter(name =>
                    (values[name] ?? '') !== '' && relevance[name]
                    && !this.evaluateExpression(relevance[name], '', values));
                if (!inactive.length) break;
                inactive.forEach(name => { values[name] = ''; });
            }
            return values;
        },

        calculationNumber(value) {
            if (value === '' || value === null || value === undefined || Array.isArray(value)) return NaN;
            if (typeof value === 'string' && !value.trim()) return NaN;
            return Number(value);
        },

        calculationText(value) {
            if (value === null || value === undefined) return '';
            if (Array.isArray(value)) return value.map(item => this.calculationText(item)).join(' ');
            return String(value);
        },

        calculationBoolean(value) {
            if (typeof value === 'number') return value !== 0 && !Number.isNaN(value);
            if (Array.isArray(value)) return value.length > 0;
            return Boolean(value);
        },

        calculationEqual(left, right) {
            if (typeof left === 'boolean' || typeof right === 'boolean') {
                return this.calculationBoolean(left) === this.calculationBoolean(right);
            }
            if (typeof left === 'number' || typeof right === 'number') {
                return this.calculationNumber(left) === this.calculationNumber(right);
            }
            return this.calculationText(left) === this.calculationText(right);
        },

        evaluateCalculation(tree, data = this.values, attributes = {}) {
            const [kind, name, args] = tree;
            if (kind === 'literal') return name;
            if (kind === 'ref') return data[name] ?? '';
            if (kind === 'attribute') return attributes[name] ?? '';
            if (kind === 'call' && name === 'choose') {
                if (args.length !== 3) throw new Error('if() requires three arguments.');
                const condition = this.calculationBoolean(this.evaluateCalculation(args[0], data, attributes));
                return this.evaluateCalculation(args[condition ? 1 : 2], data, attributes);
            }
            if (kind === 'op' && (name === 'and' || name === 'or')) {
                const evaluate = arg => this.calculationBoolean(this.evaluateCalculation(arg, data, attributes));
                return name === 'and' ? args.every(evaluate) : args.some(evaluate);
            }
            const values = args.map(arg => this.evaluateCalculation(arg, data, attributes));
            const a = this.calculationNumber(values[0]), b = this.calculationNumber(values[1]);
            if (kind === 'op') {
                switch (name) {
                    case '+': return a + b;
                    case '-': return a - b;
                    case '*': return a * b;
                    case '/': return a / b;
                    case '%': return a % b;
                    case 'neg': return -a;
                    case 'pos': return a;
                    case 'not': return !this.calculationBoolean(values[0]);
                    case '=': return this.calculationEqual(values[0], values[1]);
                    case '!=': return !this.calculationEqual(values[0], values[1]);
                    case '<': return a < b;
                    case '<=': return a <= b;
                    case '>': return a > b;
                    case '>=': return a >= b;
                }
            }
            switch (name) {
                case 'true': return true;
                case 'false': return false;
                case 'int': return Math.trunc(a);
                case 'number': return a;
                case 'string': return this.calculationText(values[0]);
                case 'substr': {
                    const start = this.calculationNumber(values[1]);
                    const end = values.length > 2 ? this.calculationNumber(values[2]) : undefined;
                    if (!Number.isFinite(start) || (end !== undefined && !Number.isFinite(end))) return '';
                    return Array.from(this.calculationText(values[0])).slice(start, end).join('');
                }
                case 'concat': return values.map(value => this.calculationText(value)).join('');
                case 'coalesce': return values.find(value => value !== '' && value !== null) ?? '';
                case 'selected': return this.calculationText(values[0]).split(/\s+/).includes(this.calculationText(values[1]));
                case 'abs': return Math.abs(a);
                case 'floor': return Math.floor(a);
                case 'ceiling': return Math.ceil(a);
                case 'round': {
                    const factor = 10 ** (values.length > 1 ? b : 0);
                    return Math.floor(a * factor + 0.5) / factor;
                }
            }
            throw new Error('Unsupported calculation expression.');
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
                input.disabled = !relevant || input.dataset.originalDisabled === 'true'
                    || input.dataset.choiceFilteredOut === 'true' || input.dataset.choiceNoOptions === 'true';
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
            return String(value ?? '').trim() !== '';
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
            this.syncChoiceFilters();
            if (Object.keys(this.calculationErrors).length || Object.keys(this.choiceFilterErrors).length) {
                event.preventDefault();
                return false;
            }
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

        evaluateExpression(expression, currentValue = '', data = this.values) {
            let expr = String(expression || '').trim();
            if (!expr) return true;
            expr = this.stripWrappingParentheses(expr);

            const notExpression = expr.match(/^not\s*\((.*)\)$/i);
            if (notExpression) {
                return !this.evaluateExpression(notExpression[1], currentValue, data);
            }

            const selected = expr.match(/^selected\(\s*\$\{([^}]+)\}\s*,\s*['"]([^'"]+)['"]\s*\)$/i);
            if (selected) {
                const values = this.asArray(data[selected[1]]);
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
                let result = this.evaluateExpression(parts[0], currentValue, data);
                for (let i = 1; i < parts.length; i += 2) {
                    const op = parts[i].toLowerCase();
                    const next = this.evaluateExpression(parts[i + 1], currentValue, data);
                    result = op === 'and' ? (result && next) : (result || next);
                }
                return result;
            }

            const comparison = expr.match(/^(\.|\$\{[^}]+\})\s*(=|!=|>=|<=|>|<)\s*(.+)$/);
            if (!comparison) return true;

            const left = this.resolveOperand(comparison[1], currentValue, data);
            const right = this.resolveOperand(comparison[3], currentValue, data);
            return this.compare(left, comparison[2], right);
        },

        resolveOperand(value, currentValue = '', data = this.values) {
            const trimmed = String(value || '').trim();
            if (trimmed === '.') return currentValue;
            if (trimmed.startsWith('${') && trimmed.endsWith('}')) {
                return data[trimmed.slice(2, -1)] ?? '';
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
