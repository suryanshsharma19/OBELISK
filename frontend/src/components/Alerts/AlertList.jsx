/**
 * Alert listing container — fetches alerts from the store,
 * renders filter bar and alert cards with pagination.
 */

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchAlerts } from '../../store/slices/alertsSlice';
import { DEFAULT_PAGE_SIZE } from '../../utils/constants';
import AlertCard from './AlertCard';
import AlertFilter from './AlertFilter';
import Pagination from '../PackageList/Pagination';
import Loader from '../common/Loader';

export default function AlertList() {
  const dispatch = useDispatch();
  const { list, total, loading } = useSelector((s) => s.alerts);

  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    threat_level: '',
    is_resolved: '',
  });

  useEffect(() => {
    const skip = (page - 1) * DEFAULT_PAGE_SIZE;
    const params = {
      skip,
      limit: DEFAULT_PAGE_SIZE,
      ...Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== ''),
      ),
    };
    dispatch(fetchAlerts(params));
  }, [dispatch, page, filters]);

  const handleFilterChange = (next) => {
    setFilters(next);
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <AlertFilter filters={filters} onChange={handleFilterChange} />
      </div>

      {loading ? (
        <Loader fullPage />
      ) : list.length === 0 ? (
        <p className="py-12 text-center text-gray-500">No alerts found</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {list.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
          <Pagination
            total={total}
            page={page}
            pageSize={DEFAULT_PAGE_SIZE}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
