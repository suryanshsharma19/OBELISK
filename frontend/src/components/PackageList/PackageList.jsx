/**
 * Package listing container — fetches packages from the store,
 * renders filter bar, cards grid, and pagination.
 */

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchPackages } from '../../store/slices/packagesSlice';
import { DEFAULT_PAGE_SIZE } from '../../utils/constants';
import PackageCard from './PackageCard';
import FilterBar from './FilterBar';
import Pagination from './Pagination';
import Loader from '../common/Loader';

export default function PackageList() {
  const dispatch = useDispatch();
  const { list, total, loading } = useSelector((s) => s.packages);

  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    threat_level: '',
    registry: '',
    sort: 'risk_score_desc',
  });

  useEffect(() => {
    const skip = (page - 1) * DEFAULT_PAGE_SIZE;
    dispatch(
      fetchPackages({
        skip,
        limit: DEFAULT_PAGE_SIZE,
        ...Object.fromEntries(
          Object.entries(filters).filter(([, v]) => v),
        ),
      }),
    );
  }, [dispatch, page, filters]);

  const handleFilterChange = (next) => {
    setFilters(next);
    setPage(1); // reset to first page on filter change
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Packages</h1>
        <FilterBar filters={filters} onChange={handleFilterChange} />
      </div>

      {loading ? (
        <Loader fullPage />
      ) : list.length === 0 ? (
        <p className="py-12 text-center text-gray-500">No packages found</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {list.map((pkg) => (
              <PackageCard key={pkg.id} pkg={pkg} />
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
